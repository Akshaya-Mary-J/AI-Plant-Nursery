const CART_KEY = 'akshayaPlantCart';

function getCart(){
    try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
    catch(e){ return []; }
}
function saveCart(cart){
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}
function updateCartCount(){
    const count = getCart().reduce((sum, item) => sum + item.quantity, 0);
    const el = document.getElementById('cartCount');
    if(el) el.textContent = count;
}
function addToCart(plant){
    const cart = getCart();
    const existing = cart.find(item => Number(item.id) === Number(plant.id));
    const maxStock = Number(plant.stock || 99);
    if(existing){
        existing.quantity = Math.min(maxStock, existing.quantity + 1);
    } else {
        cart.push({id:Number(plant.id), name:plant.name, price:Number(plant.price), emoji:plant.emoji || '🌿', stock:maxStock, quantity:1});
    }
    saveCart(cart);
    showToast(`${plant.name} added to cart`);
}
function changeQty(id, delta){
    const cart = getCart().map(item => {
        if(Number(item.id) === Number(id)) item.quantity = Math.max(1, Math.min(item.stock || 99, item.quantity + delta));
        return item;
    });
    saveCart(cart);
    renderCartPage();
}
function removeCartItem(id){
    saveCart(getCart().filter(item => Number(item.id) !== Number(id)));
    renderCartPage();
}
function clearCart(){
    saveCart([]);
    renderCartPage();
}
function totals(){
    const subtotal = getCart().reduce((sum, item) => sum + item.price * item.quantity, 0);
    const delivery = subtotal === 0 || subtotal >= 999 ? 0 : 79;
    return {subtotal, delivery, total:subtotal + delivery};
}
function currency(value){ return `₹${Number(value || 0).toLocaleString('en-IN')}`; }
function renderCartPage(){
    const container = document.getElementById('cartItems');
    if(!container) return;
    const cart = getCart();
    if(cart.length === 0){
        container.innerHTML = `<div class="empty-state"><h2>Your cart is empty</h2><p>Add plants from the shop page.</p><a class="btn primary" href="/plants">Shop Plants</a></div>`;
    } else {
        container.innerHTML = cart.map(item => `
            <div class="cart-item">
                <div class="cart-thumb">${item.emoji || '🌿'}</div>
                <div>
                    <h3>${item.name}</h3>
                    <p class="muted">${currency(item.price)} each</p>
                    <div class="qty-box">
                        <button onclick="changeQty(${item.id}, -1)">−</button>
                        <strong>${item.quantity}</strong>
                        <button onclick="changeQty(${item.id}, 1)">+</button>
                    </div>
                </div>
                <div>
                    <strong>${currency(item.price * item.quantity)}</strong><br>
                    <button class="remove-btn" onclick="removeCartItem(${item.id})">Remove</button>
                </div>
            </div>
        `).join('');
    }
    const t = totals();
    const subtotal = document.getElementById('summarySubtotal');
    const delivery = document.getElementById('summaryDelivery');
    const total = document.getElementById('summaryTotal');
    if(subtotal) subtotal.textContent = currency(t.subtotal);
    if(delivery) delivery.textContent = t.delivery ? currency(t.delivery) : 'Free';
    if(total) total.textContent = currency(t.total);
}
function showToast(message){
    let toast = document.getElementById('siteToast');
    if(!toast){
        toast = document.createElement('div');
        toast.id = 'siteToast';
        toast.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#0b3d2a;color:white;padding:12px 18px;border-radius:999px;box-shadow:0 16px 40px rgba(0,0,0,.2);z-index:200;font-weight:800;opacity:0;transition:.2s';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    setTimeout(() => toast.style.opacity = '0', 1800);
}
document.addEventListener('click', function(e){
    const btn = e.target.closest('.add-cart-btn');
    if(!btn) return;
    addToCart({id:btn.dataset.id, name:btn.dataset.name, price:btn.dataset.price, emoji:btn.dataset.emoji, stock:btn.dataset.stock});
});
document.addEventListener('DOMContentLoaded', function(){
    updateCartCount();
    const clearBtn = document.getElementById('clearCartBtn');
    if(clearBtn) clearBtn.addEventListener('click', clearCart);
});
