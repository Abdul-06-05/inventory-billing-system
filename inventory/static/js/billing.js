// Billing page: builds the cart in the browser, then sends it to Django as JSON.
const products = JSON.parse(document.getElementById("products-data").textContent);
const select = document.getElementById("product-select");
const qtyInput = document.getElementById("qty");
const hint = document.getElementById("stock-hint");
const tbody = document.querySelector("#cart-table tbody");
const gstInput = document.getElementById("gst");
const errorBox = document.getElementById("error");

let cart = []; // [{id, name, price, stock, qty}]

function findProduct(id) {
  return products.find((p) => p.id === Number(id));
}

function showHint() {
  const p = findProduct(select.value);
  hint.textContent = p ? `In stock: ${p.stock} | ₹${p.price}` : "";
}

function render() {
  tbody.innerHTML = "";
  let subtotal = 0;
  cart.forEach((item, index) => {
    const line = item.price * item.qty;
    subtotal += line;
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${item.name}</td><td>₹${item.price.toFixed(2)}</td>
      <td>${item.qty}</td><td>₹${line.toFixed(2)}</td>
      <td><button class="btn red small" data-index="${index}" type="button">Remove</button></td>`;
    tbody.appendChild(tr);
  });
  const gst = (subtotal * (Number(gstInput.value) || 0)) / 100;
  document.getElementById("subtotal").textContent = subtotal.toFixed(2);
  document.getElementById("gst-amount").textContent = gst.toFixed(2);
  document.getElementById("grand").textContent = (subtotal + gst).toFixed(2);
}

document.getElementById("add-btn").addEventListener("click", () => {
  errorBox.textContent = "";
  const p = findProduct(select.value);
  const qty = parseInt(qtyInput.value, 10);
  if (!p || !qty || qty < 1) return;

  const existing = cart.find((c) => c.id === p.id);
  const newQty = (existing ? existing.qty : 0) + qty;
  if (newQty > p.stock) {
    errorBox.textContent = `Only ${p.stock} of ${p.name} in stock.`;
    return;
  }
  if (existing) existing.qty = newQty;
  else cart.push({ ...p, qty });
  render();
});

tbody.addEventListener("click", (e) => {
  if (e.target.dataset.index !== undefined) {
    cart.splice(Number(e.target.dataset.index), 1);
    render();
  }
});

gstInput.addEventListener("input", render);
select.addEventListener("change", showHint);

document.getElementById("save-btn").addEventListener("click", async () => {
  errorBox.textContent = "";
  const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
  const response = await fetch("/billing/save/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
    body: JSON.stringify({
      customer_name: document.getElementById("cust-name").value,
      customer_phone: document.getElementById("cust-phone").value,
      gst_percent: gstInput.value,
      items: cart.map((c) => ({ product_id: c.id, quantity: c.qty })),
    }),
  });
  const data = await response.json();
  if (response.ok) window.location.href = data.url; // go to the invoice page
  else errorBox.textContent = data.error;
});

showHint();
render();
