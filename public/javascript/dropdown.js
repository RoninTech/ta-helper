// Script to hide/show menu
var span = document.querySelector('span#about_chevron');
var menu = document.querySelector('ul.sub-menu');
    span.addEventListener('click', function (event) {
        if (menu.classList.contains('dn')) {
            //menu.style.display = "none";
            //span.innerHTML = "Show Menu";
            menu.classList.remove('dn');
        } else {
            // menu.style.display = "";
            // span.innerHTML = "Hide Menu";
            menu.classList.add('dn');
        }
    }
);