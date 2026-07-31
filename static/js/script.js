document.addEventListener('DOMContentLoaded', function(){
    const menuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    if(menuBtn && navLinks){
        menuBtn.addEventListener('click', () => navLinks.classList.toggle('open'));
    }
});
