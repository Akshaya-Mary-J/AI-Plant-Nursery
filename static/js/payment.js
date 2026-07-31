function renderCheckoutPreview(){
    const list = document.getElementById('checkoutItems');
    if(!list) return;
    const cart = getCart();
    if(cart.length === 0){
        list.innerHTML = '<p class="muted">Your cart is empty. Please add plants before checkout.</p>';
    } else {
        list.innerHTML = cart.map(item => `<div class="checkout-mini"><span>${item.emoji || '🌿'} ${item.name} × ${item.quantity}</span><strong>${currency(item.price * item.quantity)}</strong></div>`).join('');
    }
    const t = totals();
    document.getElementById('checkoutSubtotal').textContent = currency(t.subtotal);
    document.getElementById('checkoutDelivery').textContent = t.delivery ? currency(t.delivery) : 'Free';
    document.getElementById('checkoutTotal').textContent = currency(t.total);
}
function getCheckoutPayload(form){
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.items = getCart();
    return data;
}
async function createCodOrder(payload){
    const res = await fetch('/api/order', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    return res.json();
}
async function createRazorpayOrder(payload){
    const res = await fetch('/api/payment/create-razorpay-order', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({items:getCart()})});
    const data = await res.json();
    if(!data.success) throw new Error(data.message || 'Razorpay order failed');
    return data;
}
async function handleCheckoutSubmit(e){
    e.preventDefault();
    const result = document.getElementById('orderResult');
    const payload = getCheckoutPayload(e.target);
    if(getCart().length === 0){
        result.innerHTML = 'Cart is empty. Please add plants first.';
        return;
    }
    result.innerHTML = 'Processing order...';
    if(payload.payment_method === 'cod'){
        const data = await createCodOrder(payload);
        if(data.success){
            clearCart();
            renderCheckoutPreview();
            result.innerHTML = `<strong>Order Placed Successfully!</strong><p>Order No: ${data.order_no}</p><p>Total: ${currency(data.total)}</p><p>Payment: Cash on Delivery</p>`;
            speakText('Order placed successfully. Thank you for shopping with Akshaya AI Plant Shop.');
        } else {
            result.innerHTML = data.message || 'Order failed.';
        }
        return;
    }
    try{
        const rzOrder = await createRazorpayOrder(payload);
        const options = {
            key: rzOrder.key_id,
            amount: rzOrder.amount,
            currency: rzOrder.currency,
            name: 'Akshaya AI Plant Shop',
            description: 'Plant Purchase',
            order_id: rzOrder.order_id,
            prefill: {name:payload.customer_name, email:payload.email, contact:payload.phone},
            theme: {color:'#1f7a4c'},
            handler: async function(response){
                const verifyRes = await fetch('/api/payment/verify', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(response)});
                const verifyData = await verifyRes.json();
                if(verifyData.success){
                    payload.payment_method = 'razorpay';
                    payload.payment_verified = true;
                    payload.razorpay_order_id = response.razorpay_order_id;
                    payload.razorpay_payment_id = response.razorpay_payment_id;
                    const orderData = await createCodOrder(payload);
                    if(orderData.success){
                        clearCart();
                        renderCheckoutPreview();
                        result.innerHTML = `<strong>Online Payment Successful!</strong><p>Order No: ${orderData.order_no}</p><p>Payment ID: ${response.razorpay_payment_id}</p>`;
                    }
                } else {
                    result.innerHTML = verifyData.message || 'Payment verification failed.';
                }
            }
        };
        const rzp = new Razorpay(options);
        rzp.open();
    }catch(err){
        result.innerHTML = err.message;
    }
}
function initCheckoutPage(){
    renderCheckoutPreview();
    const form = document.getElementById('checkoutForm');
    if(form) form.addEventListener('submit', handleCheckoutSubmit);
}
