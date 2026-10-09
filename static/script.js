function switchTab(tabId, element) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.querySelectorAll('.view-section').forEach(section => section.classList.remove('active'));
    if(element) element.classList.add('active');
    document.getElementById(tabId).classList.add('active');
    localStorage.setItem('activeTab', tabId);
}

window.addEventListener('DOMContentLoaded', () => {
    const savedTab = localStorage.getItem('activeTab');
    if(savedTab) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            if(item.getAttribute('onclick').includes(savedTab)) {
                switchTab(savedTab, item);
            }
        });
    }
    loadChatHistory();
});

function openModal() { document.getElementById('addCustomerModal').style.display = 'flex'; }
function closeModal() { document.getElementById('addCustomerModal').style.display = 'none'; }

function openTicketModal() { document.getElementById('addTicketModal').style.display = 'flex'; }
function closeTicketModal() { document.getElementById('addTicketModal').style.display = 'none'; }

window.onload = function() {
    const ctxSales = document.getElementById('salesChart').getContext('2d');
    new Chart(ctxSales, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Revenue (EGP)',
                data: [12000, 19000, 15000, 25000, 32000, 45000],
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.3
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    const ctxLeads = document.getElementById('leadsChart').getContext('2d');
    new Chart(ctxLeads, {
        type: 'doughnut',
        data: {
            labels: ['Hot', 'Warm', 'Cold'],
            datasets: [{
                data: [12, 19, 7],
                backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6']
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
};

function saveChatHistory(htmlContent) {
    localStorage.setItem('chatHistory', htmlContent);
}

function loadChatHistory() {
    const history = localStorage.getItem('chatHistory');
    if(history) {
        document.getElementById('chatMessages').innerHTML = history;
    }
}

function triggerAIPrompt(messageText) {
    switchTab('ai', document.querySelectorAll('.nav-item')[5]);
    const inputField = document.getElementById('userInput');
    inputField.value = messageText;
    sendToAI();
}

function sendViaWhatsApp(btn, phone) {
    const msgParagraph = btn.parentElement.previousElementSibling;
    const textMessage = encodeURIComponent(msgParagraph.innerText);
    
    if (!phone || phone === "None") {
        phone = "201000000000";
    }
    
    const whatsappUrl = `https://wa.me/${phone}?text=${textMessage}`;
    window.open(whatsappUrl, '_blank');
    
    btn.innerText = "✓ Sent to WhatsApp!";
    btn.style.backgroundColor = "#059669";
}

function sendToAI() {
    const inputField = document.getElementById('userInput');
    const question = inputField.value.trim();
    if (!question) return;

    const chatMessages = document.getElementById('chatMessages');

    chatMessages.innerHTML += `<div class="msg user">${question}</div>`;
    inputField.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    fetch('/ask_ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'question=' + encodeURIComponent(question)
    })
    .then(response => response.text())
    .then(rawResponse => {
        let parts = rawResponse.split('---PHONE:');
        let aiReply = parts[0];
        let phoneNum = parts[1] || "";

        chatMessages.innerHTML += `
            <div class="msg ai">
                <p>${aiReply}</p>
                <div class="ai-actions">
                    <button class="whatsapp" onclick="sendViaWhatsApp(this, '${phoneNum}')">💬 Send via WhatsApp</button>
                    <button class="translate-btn" onclick="translateMessage(this)">🌐 Translate to Arabic</button>
                </div>
            </div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
        saveChatHistory(chatMessages.innerHTML);
    });
}

function translateMessage(btn) {
    const msgParagraph = btn.parentElement.previousElementSibling;
    const originalText = msgParagraph.innerText;

    fetch('/translate_ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'text=' + encodeURIComponent(originalText)
    })
    .then(res => res.text())
    .then(translated => {
        msgParagraph.innerText = translated;
        btn.innerText = "🌐 Translated to Arabic";
        saveChatHistory(document.getElementById('chatMessages').innerHTML);
    });
}