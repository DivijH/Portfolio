var modalEle = document.querySelector(".modal");
var modalImage = document.querySelector(".modal-image");
var caption = document.querySelector(".caption");

Array.from(document.querySelectorAll(".gallery-image")).forEach(item => {
    item.addEventListener("click", event => {
        modalEle.style.display = "block";
        modalImage.src = event.target.src;
        caption.innerText = event.target.alt;
    });
});

document.querySelector(".close").addEventListener("click", () => {
    modalEle.style.display = "none";
});