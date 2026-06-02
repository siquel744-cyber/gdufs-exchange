const productGrid = document.getElementById("productGrid");
const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const resultCount = document.getElementById("resultCount");
const publishModal = document.getElementById("publishModal");
const openPublish = document.getElementById("openPublish");
const closePublish = document.getElementById("closePublish");
const cancelPublish = document.getElementById("cancelPublish");
const publishForm = document.getElementById("publishForm");
const imageInput = document.getElementById("imageInput");
const imageFileInput = document.getElementById("imageFileInput");
const authModal = document.getElementById("loginModal");
const openLogin = document.getElementById("openLogin");
const closeLogin = document.getElementById("closeLogin");
const cancelLogin = document.getElementById("cancelLogin");
const authForm = document.getElementById("authForm");
const authUsername = document.getElementById("authUsername");
const authPassword = document.getElementById("authPassword");
const registerMode = document.getElementById("registerMode");
const authSubmit = document.getElementById("authSubmit");
const usernameDisplay = document.getElementById("usernameDisplay");
const userPanel = document.getElementById("userPanel");
const logoutButton = document.getElementById("logoutButton");

let currentUser = null;

function formatPrice(price) {
  return `¥${price}`;
}

function showAlert(message) {
  window.alert(message);
}

async function apiGetSession() {
  const response = await fetch("/api/session");
  return response.json();
}

async function apiFetchProducts(query = "") {
  const url = query ? `/api/products?q=${encodeURIComponent(query)}` : "/api/products";
  const response = await fetch(url);
  return response.json();
}

async function apiPostJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

async function apiUploadImage(file) {
  const formData = new FormData();
  formData.append("image", file);
  const response = await fetch("/api/upload-image", {
    method: "POST",
    body: formData,
  });
  return response.json();
}

function renderProducts(list) {
  const items = list.map((product) => {
    const soldBadge = product.sold ? '<div class="sold-badge">已售出</div>' : "";
    const canMarkSold = currentUser && product.owner_id === currentUser.id && !product.sold;
    const actionButton = canMarkSold
      ? `<div class="card-actions"><button class="secondary-button small mark-sold-button" data-product-id="${product.id}" type="button">标记售出</button></div>`
      : "";

    return `
      <article class="product-card">
        ${soldBadge}
        <div class="image-wrap">
          <img src="${product.image_url}" alt="${product.title}" loading="lazy" />
          ${product.sold ? '<div class="sold-overlay">已售出</div>' : ''}
        </div>
        <div class="card-body">
          <div class="card-meta">
            <div>
              <p class="card-category">${product.category}</p>
              <h3 class="card-title">${product.title}</h3>
            </div>
            <div class="price-tag">${formatPrice(product.price)}</div>
          </div>
          <p class="card-desc">${product.description}</p>
          <div class="seller-info">
            <span>卖家：${product.seller}</span>
            <span class="contact-chip">${product.contact}</span>
          </div>
          ${actionButton}
        </div>
      </article>
    `;
  });

  productGrid.innerHTML = items.join("");
  resultCount.textContent = `共 ${list.length} 件商品可浏览`;
}

function toggleModal(modal, show) {
  const visible = show !== undefined ? show : modal.classList.contains("hidden");
  modal.classList.toggle("hidden", !visible);
  document.body.style.overflow = visible ? "hidden" : "";
}

function updateAuthPanel() {
  if (currentUser) {
    userPanel.classList.remove("hidden");
    openLogin.classList.add("hidden");
    usernameDisplay.textContent = currentUser.username;
    authSubmit.textContent = "登录";
    registerMode.checked = false;
  } else {
    userPanel.classList.add("hidden");
    openLogin.classList.remove("hidden");
  }
}

async function loadSession() {
  const sessionData = await apiGetSession();
  currentUser = sessionData.logged_in ? { id: sessionData.user_id, username: sessionData.username, is_admin: sessionData.is_admin, is_banned: sessionData.is_banned } : null;
  // show admin link if admin
  const adminLink = document.getElementById("adminLink");
  if (adminLink) {
    if (currentUser && currentUser.is_admin) adminLink.classList.remove('hidden');
    else adminLink.classList.add('hidden');
  }
  updateAuthPanel();
}

async function loadProducts() {
  const products = await apiFetchProducts(searchInput.value);
  renderProducts(products);
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  const username = authUsername.value.trim();
  const password = authPassword.value.trim();
  if (!username || !password) {
    showAlert("请输入用户名和密码。");
    return;
  }

  const path = registerMode.checked ? "/api/register" : "/api/login";
  const result = await apiPostJson(path, { username, password });
  if (result.error) {
    showAlert(result.error);
    return;
  }

  if (registerMode.checked) {
    showAlert("注册成功，请登录。登录后即可发布商品。");
    registerMode.checked = false;
    authSubmit.textContent = "登录";
    return;
  }

  currentUser = { id: result.user_id, username: result.username };
  updateAuthPanel();
  toggleModal(authModal, false);
  authForm.reset();
  await loadProducts();
}

async function handlePublishSubmit(event) {
  event.preventDefault();

  if (!currentUser) {
    toggleModal(authModal, true);
    return;
  }

  const title = document.getElementById("titleInput").value.trim();
  const price = Number(document.getElementById("priceInput").value);
  const contact = document.getElementById("contactInput").value.trim();
  const category = document.getElementById("categoryInput").value;
  const description = document.getElementById("descriptionInput").value.trim() || "暂无补充描述。";
  const imageUrl = imageInput.value.trim();
  const imageFile = imageFileInput.files[0];

  if (!title || !price || !contact || (!imageUrl && !imageFile)) {
    showAlert("请补全商品名称、价格、联系方式和图片链接或上传图片。");
    return;
  }

  let finalImageUrl = imageUrl;
  if (!finalImageUrl && imageFile) {
    const uploadResult = await apiUploadImage(imageFile);
    if (uploadResult.error) {
      showAlert(uploadResult.error);
      return;
    }
    finalImageUrl = uploadResult.image_url;
  }

  const result = await apiPostJson("/api/products", {
    title,
    price,
    contact,
    category,
    image_url: finalImageUrl,
    description,
  });

  if (result.error) {
    showAlert(result.error);
    return;
  }

  publishForm.reset();
  imageFileInput.value = "";
  toggleModal(publishModal, false);
  await loadProducts();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function handleMarkSold(productId) {
  const result = await apiPostJson(`/api/products/${productId}/sold`, {});
  if (result.error) {
    showAlert(result.error);
    return;
  }
  await loadProducts();
}

function updateLoginMode() {
  authSubmit.textContent = registerMode.checked ? "注册" : "登录";
}

searchInput.addEventListener("input", loadProducts);
searchButton.addEventListener("click", loadProducts);
openPublish.addEventListener("click", () => {
  if (!currentUser) {
    toggleModal(authModal, true);
    return;
  }
  toggleModal(publishModal, true);
});
closePublish.addEventListener("click", () => toggleModal(publishModal, false));
cancelPublish.addEventListener("click", () => toggleModal(publishModal, false));
openLogin.addEventListener("click", () => toggleModal(authModal, true));
logoutButton.addEventListener("click", async () => {
  const result = await apiPostJson("/api/logout", {});
  if (result.success) {
    currentUser = null;
    updateAuthPanel();
    await loadProducts();
  }
});
closeLogin.addEventListener("click", () => toggleModal(authModal, false));
cancelLogin.addEventListener("click", () => toggleModal(authModal, false));
registerMode.addEventListener("change", updateLoginMode);

productGrid.addEventListener("click", (event) => {
  if (event.target.matches(".mark-sold-button")) {
    const productId = Number(event.target.dataset.productId);
    handleMarkSold(productId);
  }
});

authForm.addEventListener("submit", handleAuthSubmit);
publishForm.addEventListener("submit", handlePublishSubmit);

window.addEventListener("DOMContentLoaded", async () => {
  await loadSession();
  await loadProducts();
});
