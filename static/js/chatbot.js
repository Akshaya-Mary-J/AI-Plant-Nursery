const CHAT_HISTORY_KEY = 'akshayaPlantChatHistoryV2';
const CHAT_SOUND_KEY = 'akshayaPlantChatSound';
let lastVoiceInput = false;

function escapeHTML(value){
    return String(value || '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

function getChatHistory(){
    try { return JSON.parse(localStorage.getItem(CHAT_HISTORY_KEY)) || []; }
    catch(e){ return []; }
}

function saveChatHistory(history){
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history.slice(-40)));
}

function isSoundEnabled(){
    const value = localStorage.getItem(CHAT_SOUND_KEY);
    return value === null ? true : value === 'true';
}

function setChatStatus(text){
    const status = document.getElementById('chatStatus');
    if(status) status.textContent = text;
}

function renderPlantCards(cards){
    if(!cards || !cards.length) return '';
    return `<div class="chat-card-grid">${cards.map(card => `
        <article class="chat-plant-card">
            <div class="chat-plant-emoji">${escapeHTML(card.emoji || '🌿')}</div>
            <div class="chat-plant-info">
                <strong>${escapeHTML(card.name)}</strong>
                <small>${escapeHTML(card.category || 'Plant')} • ₹${Number(card.price || 0).toLocaleString('en-IN')}</small>
                <span>${escapeHTML(card.subtitle || 'Easy care plant')}</span>
                <div class="chat-card-actions">
                    <a href="${escapeHTML(card.url || `/plant/${card.id}`)}">View</a>
                    <button type="button" class="chat-add-cart" data-id="${escapeHTML(card.id)}" data-name="${escapeHTML(card.name)}" data-price="${escapeHTML(card.price)}" data-emoji="${escapeHTML(card.emoji || '🌿')}" data-stock="${escapeHTML(card.stock || 99)}">Add</button>
                </div>
            </div>
        </article>
    `).join('')}</div>`;
}

function appendChatMessage(text, type, options = {}){
    const box = document.getElementById('chatMessages');
    if(!box) return;
    const div = document.createElement('div');
    div.className = type === 'user' ? 'user-msg' : 'bot-msg rich-msg';
    div.innerHTML = type === 'user'
        ? escapeHTML(text)
        : `<span>${escapeHTML(text)}</span>${renderPlantCards(options.cards || [])}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;

    if(!options.skipSave){
        const history = getChatHistory();
        history.push({text, type, cards: options.cards || []});
        saveChatHistory(history);
    }
}

function addTypingIndicator(){
    const box = document.getElementById('chatMessages');
    if(!box) return null;
    const div = document.createElement('div');
    div.className = 'bot-msg typing-msg';
    div.innerHTML = '<span></span><span></span><span></span>';
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    setChatStatus('Typing a helpful reply...');
    return div;
}

function renderSuggestions(suggestions){
    const wrap = document.getElementById('chatSuggestions');
    if(!wrap) return;
    const clean = (suggestions && suggestions.length ? suggestions : [
        'Suggest beginner plants', 'Plants under 300', 'Why are leaves yellow?'
    ]).slice(0, 5);
    wrap.innerHTML = clean.map(q => `<button type="button" data-question="${escapeHTML(q)}">${escapeHTML(q)}</button>`).join('');
}

async function sendChatMessage(message, options = {}){
    const clean = (message || '').trim();
    if(!clean) return;

    if(options.fromVoice) lastVoiceInput = true;
    appendChatMessage(clean, 'user');

    const input = document.getElementById('chatInput');
    if(input) input.value = '';

    const typing = addTypingIndicator();
    try{
        const res = await fetch('/chatbot', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({message:clean})
        });
        const data = await res.json();
        if(typing) typing.remove();
        setChatStatus(`Intent: ${data.intent || 'general'} • ready for next question`);
        appendChatMessage(data.reply || 'I could not prepare a reply. Please try again.', 'bot', {cards:data.cards || []});
        renderSuggestions(data.suggestions || []);
        if(isSoundEnabled() || lastVoiceInput){
            speakText(data.speak || data.reply || '');
        }
        lastVoiceInput = false;
    }catch(err){
        if(typing) typing.remove();
        setChatStatus('Connection issue');
        appendChatMessage('Sorry, chatbot connection failed. Please check whether your Flask server is running.', 'bot');
    }
}

function speakText(text){
    if(!('speechSynthesis' in window) || !text) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text.replace(/₹/g, 'rupees '));
    utter.lang = 'en-IN';
    utter.rate = 0.95;
    utter.pitch = 1;
    window.speechSynthesis.speak(utter);
}

function updateSoundButton(){
    const btn = document.getElementById('soundBtn');
    if(!btn) return;
    btn.textContent = isSoundEnabled() ? '🔊' : '🔇';
    btn.title = isSoundEnabled() ? 'Voice reply is ON' : 'Voice reply is OFF';
}

function setupVoiceAssistant(){
    const voiceBtn = document.getElementById('voiceBtn');
    const input = document.getElementById('chatInput');
    if(!voiceBtn) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(!SpeechRecognition){
        voiceBtn.title = 'Voice assistant is not supported in this browser';
        voiceBtn.addEventListener('click', () => appendChatMessage('Voice input works best in Google Chrome. You can still type your question.', 'bot'));
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    voiceBtn.addEventListener('click', function(){
        try{
            voiceBtn.classList.add('listening');
            setChatStatus('Listening... speak your plant question');
            recognition.start();
        }catch(e){
            voiceBtn.classList.remove('listening');
        }
    });

    recognition.onresult = function(event){
        let interim = '';
        let finalText = '';
        for(let i = event.resultIndex; i < event.results.length; i++){
            const transcript = event.results[i][0].transcript;
            if(event.results[i].isFinal) finalText += transcript;
            else interim += transcript;
        }
        if(input) input.value = finalText || interim;
        if(finalText.trim()) sendChatMessage(finalText, {fromVoice:true});
    };

    recognition.onerror = function(){
        appendChatMessage('I could not hear clearly. Please try again or type your question.', 'bot');
    };

    recognition.onend = function(){
        voiceBtn.classList.remove('listening');
        setChatStatus('Online • plant care, shopping and disease help');
    };
}

function loadPreviousChat(){
    const history = getChatHistory();
    const box = document.getElementById('chatMessages');
    if(!box || !history.length) return;
    box.innerHTML = '';
    history.forEach(item => appendChatMessage(item.text, item.type, {cards:item.cards || [], skipSave:true}));
}

async function clearChat(){
    localStorage.removeItem(CHAT_HISTORY_KEY);
    try{ await fetch('/chatbot/reset', {method:'POST'}); }catch(e){}
    const box = document.getElementById('chatMessages');
    if(box){
        box.innerHTML = '';
        appendChatMessage('Chat cleared. Ask me anything about plants, care, disease, cart or payment.', 'bot');
    }
    renderSuggestions(['Suggest beginner plants', 'Plants under 300', 'Why are leaves turning yellow?']);
}

document.addEventListener('DOMContentLoaded', function(){
    const toggle = document.getElementById('chatToggle');
    const panel = document.getElementById('chatPanel');
    const close = document.getElementById('closeChat');
    const form = document.getElementById('chatForm');
    const soundBtn = document.getElementById('soundBtn');
    const clearBtn = document.getElementById('clearChat');

    loadPreviousChat();
    updateSoundButton();

    if(toggle && panel) toggle.addEventListener('click', () => {
        panel.classList.toggle('open');
        if(panel.classList.contains('open')){
            const input = document.getElementById('chatInput');
            setTimeout(() => input && input.focus(), 150);
        }
    });
    if(close && panel) close.addEventListener('click', () => panel.classList.remove('open'));
    if(form) form.addEventListener('submit', function(e){
        e.preventDefault();
        sendChatMessage(document.getElementById('chatInput').value);
    });
    if(soundBtn) soundBtn.addEventListener('click', function(){
        localStorage.setItem(CHAT_SOUND_KEY, String(!isSoundEnabled()));
        updateSoundButton();
    });
    if(clearBtn) clearBtn.addEventListener('click', clearChat);

    document.addEventListener('click', function(e){
        const suggestion = e.target.closest('#chatSuggestions button');
        if(suggestion){
            sendChatMessage(suggestion.dataset.question || suggestion.textContent);
            return;
        }
        const addBtn = e.target.closest('.chat-add-cart');
        if(addBtn && typeof addToCart === 'function'){
            addToCart({
                id:addBtn.dataset.id,
                name:addBtn.dataset.name,
                price:addBtn.dataset.price,
                emoji:addBtn.dataset.emoji,
                stock:addBtn.dataset.stock
            });
            appendChatMessage(`${addBtn.dataset.name} added to your cart. You can continue shopping or checkout.`, 'bot');
            renderSuggestions(['Checkout help', 'Payment options', 'Suggest similar plants']);
        }
    });

    setupVoiceAssistant();
});
