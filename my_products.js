const productGrid = document.getElementById("productGrid");
const resultCount = document.getElementById("resultCount");
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

async function apiFetchMyProducts() {
  const response = await fetch("/api/my-products");
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

function renderProducts(list) {
  const items = list.map((product) => {
    const soldBadge = product.sold ? '<div class="sold-badge">已售出</div>' : '';
    const actionButton = product.sold
      ? ''
      : `<div class="card-actions"><button class="secondary-button small mark-sold-button" data-product-id="${product.id}" type="button">标记售出</button></div>`;

    return `
      <article class="product-card">
        ${soldBadge}
        <img src="${product.image_url}" alt="${product.title}" loading="lazy" />
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
  resultCount.textContent = `共 ${list.length} 件商品`;
}

function updateAuthPanel() {
  if (currentUser) {
    userPanel.classList.remove("hidden");
    usernameDisplay.textContent = currentUser.username;
  } else {
    userPanel.classList.add("hidden");
  }
}

async function loadSession() {
  const sessionData = await apiGetSession();
  currentUser = sessionData.logged_in ? { id: sessionData.user_id, username: sessionData.username } : null;
  updateAuthPanel();
  if (!currentUser) {
    showAlert("请先登录后查看我的商品。");
    window.location.href = "/";
  }
}

async function loadProducts() {
  const products = await apiFetchMyProducts();
  if (products.error) {
    showAlert(products.error);
    return;
  }
  renderProducts(products);
}

async function handleMarkSold(productId) {
  const result = await apiPostJson(`/api/products/${productId}/sold`, {});
  if (result.error) {
    showAlert(result.error);
    return;
  }
  await loadProducts();
}

productGrid.addEventListener("click", (event) => {
  if (event.target.matches(".mark-sold-button")) {
    const productId = Number(event.target.dataset.productId);
    handleMarkSold(productId);
  }
});

logoutButton.addEventListener("click", async () => {
  await apiPostJson("/api/logout", {});
  window.location.href = "/";
});

window.addEventListener("DOMContentLoaded", async () => {
  await loadSession();
  await loadProducts();
});
