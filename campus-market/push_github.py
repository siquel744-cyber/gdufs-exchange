import os
import json
import base64
import urllib.request
import urllib.error

TOKEN = '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'
REPO = 'sique1744-cyber/gdufs-exchange'
ROOT = r'C:\Users\33674\Desktop\campus-market'
SKIP = {'push_github.py'}

API = 'https://api.github.com/repos/' + REPO

headers = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'github-api-upload-script'
}


def request(method, path, data=None):
    url = API + path
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8')
        raise RuntimeError(f'HTTP {e.code} {e.reason} {msg}')


def list_files():
    entries = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '.git' in dirpath.split(os.sep):
            continue
        for fname in filenames:
            if fname in SKIP:
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, ROOT).replace(os.sep, '/')
            entries.append((rel, full))
    return sorted(entries)


def main():
    print('Listing files...')
    files = list_files()
    if not files:
        raise RuntimeError('No files found to push')
    print(f'Found {len(files)} files')

    ref = None
    try:
        ref = request('GET', '/git/ref/heads/main')
        print('Found existing main branch')
    except RuntimeError as exc:
        if 'HTTP 404' in str(exc):
            print('main branch not found; will create a new branch')
            ref = None
        else:
            raise

    base_sha = None
    if ref:
        base_sha = ref['object']['sha']
        print('Base SHA:', base_sha)

    print('Creating blobs...')
    blobs = {}
    for rel, full in files:
        with open(full, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('utf-8')
        blob = request('POST', '/git/blobs', {'content': b64, 'encoding': 'base64'})
        blobs[rel] = blob['sha']
    print('Created', len(blobs), 'blobs')

    tree = [
        {'path': rel, 'mode': '100644', 'type': 'blob', 'sha': sha}
        for rel, sha in blobs.items()
    ]
    print('Creating tree...')
    tree_resp = request('POST', '/git/trees', {'tree': tree, 'base_tree': base_sha} if base_sha else {'tree': tree})
    tree_sha = tree_resp['sha']
    print('Tree SHA:', tree_sha)

    print('Creating commit...')
    commit_message = 'Deploy project to GitHub via API'
    commit_data = {'message': commit_message, 'tree': tree_sha}
    if base_sha:
        commit_data['parents'] = [base_sha]
    commit = request('POST', '/git/commits', commit_data)
    commit_sha = commit['sha']
    print('Commit SHA:', commit_sha)

    if ref:
        print('Updating main branch ref...')
        request('PATCH', '/git/refs/heads/main', {'sha': commit_sha, 'force': False})
    else:
        print('Creating main branch ref...')
        request('POST', '/git/refs', {'ref': 'refs/heads/main', 'sha': commit_sha})
    print('Push completed')

if __name__ == '__main__':
    main()
