const introDiv = document.getElementById('intro');
introDiv.setAttribute('style', 'height:'+screen.height*0.6+'px');

const canvas = document.getElementById('matrixBackground');
const ctx = canvas.getContext('2d');
canvas.height = introDiv.offsetHeight;
canvas.width = introDiv.offsetWidth;

class Symbol {
    constructor(x, y, fontSize, canvasHeight) {
        this.characters = "1234567890qwertyuioplkjhgfdsazxcvbnmQWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+=|}]{[:;?/>.<,~`";
        this.x = x;
        this.y = y;
        this.fontSize = fontSize;
        this.text = '';
        this.canvasHeight = canvasHeight;
    }
    draw(context) {
        this.text = this.characters.charAt(Math.floor(Math.random()*this.characters.length));
        context.fillText(this.text, this.x*this.fontSize, this.y*this.fontSize);
        if(this.y*this.fontSize > this.canvasHeight && Math.random() > 0.98) {
            this.y = 0;
        } else {
            this.y += 1;
        }
    }
}

class Effect {
    constructor(canvasWidth, canvasHeight) {
        this.canvasWidth = canvasWidth;
        this.canvasHeight = canvasHeight;
        this.fontSize = 25;
        this.columns = this.canvasWidth/this.fontSize;
        this.symbols = [];
        this.#initialize();
    }
    #initialize() {
        for(let i=0; i<this.columns; i++) {
            this.symbols[i] = new Symbol(i, 0, this.fontSize, this.canvasHeight);
        }
    }
    resize(width, height) {
        this.canvasHeight = height;
        this.canvasWidth = width;
        this.columns = this.canvasWidth/this.fontSize;
        this.symbols = [];
        this.#initialize();
    }
}

const effect = new Effect(canvas.width, canvas.height);
let lastTime = 0;
const fps = 40;
const nextFrame = 1000/fps;
let timer = 0;

function animate(timestamp) {
    const deltaTime = timestamp - lastTime;
    lastTime = timestamp;
    if(timer > nextFrame) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.textAlign = 'center';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#0aff0a';
        ctx.font = effect.fontSize + 'px monospace';
        effect.symbols.forEach(symbol => symbol.draw(ctx));
        timer = 0;
    } else {
        timer += deltaTime;
    }
    requestAnimationFrame(animate);
}
animate(0);

window.addEventListener('resize', function() {
    canvas.height = document.querySelector('#intro').offsetHeight;
    canvas.width = document.querySelector('#intro').offsetWidth;
    effect.resize(canvas.width, canvas.height);
})