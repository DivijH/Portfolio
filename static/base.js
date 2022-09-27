function burgerToggle() {
    const hiddenLinks = document.getElementsByClassName('hidden-links');
    // const hiddenLinks = document.getElementById('trial');
    if(hiddenLinks[0].style.display === 'block') {
        changeDisplay(hiddenLinks, 'none');
    } else {
        changeDisplay(hiddenLinks, 'block');
    }
}

function changeDisplay(classList, display) {
    for(var i=0; i<classList.length; i++) {
        classList[i].style.display = display;
    }
}