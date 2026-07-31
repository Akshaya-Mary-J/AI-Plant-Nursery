const REMINDER_KEY = 'akshayaPlantReminders';
function getReminders(){
    try{return JSON.parse(localStorage.getItem(REMINDER_KEY)) || []}catch(e){return []}
}
function saveReminder(){
    const plant = document.getElementById('reminderPlant').value.trim();
    const date = document.getElementById('reminderDate').value;
    if(!plant || !date){alert('Please enter plant name and reminder date');return;}
    const reminders = getReminders();
    reminders.push({plant, date});
    localStorage.setItem(REMINDER_KEY, JSON.stringify(reminders));
    renderReminders();
}
function renderReminders(){
    const list = document.getElementById('reminderList');
    if(!list) return;
    const reminders = getReminders();
    list.innerHTML = reminders.length ? reminders.map((r,i)=>`<p><strong>${r.plant}</strong> watering reminder on ${r.date} <button onclick="deleteReminder(${i})">Remove</button></p>`).join('') : '<p class="muted">No reminders saved.</p>';
}
function deleteReminder(index){
    const reminders = getReminders();
    reminders.splice(index,1);
    localStorage.setItem(REMINDER_KEY, JSON.stringify(reminders));
    renderReminders();
}
document.addEventListener('DOMContentLoaded', renderReminders);
