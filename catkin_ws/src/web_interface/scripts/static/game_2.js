const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const feedback = document.getElementById('feedback');
const startButton = document.getElementById('startButton');
const leftButton = document.getElementById('leftButton');
const rightButton = document.getElementById('rightButton');
const timeDisplay = document.getElementById('time'); 
const pauseButton = document.getElementById('pauseButton');
const resumeButton = document.getElementById('resumeButton');
let isPaused = false;


canvas.width = 800;
canvas.height = 600;

let gameInterval;
let timeInterval;
let score = 0;
let timeRemaining = 60; // Tiempo del juego en segundos
let attentionObjects = [];
let objectSpeed = 2; // Aumenta la velocidad de los objetos

// Posición inicial del jugador
let playerX = canvas.width / 2;
const playerY = canvas.height - 80;
const playerWidth = 80;
const playerHeight = 80;
const playerSpeed = 15; // Aumenta la velocidad del jugador

let moveLeftInterval;
let moveRightInterval;

startButton.addEventListener('click', startGame);

leftButton.addEventListener('mousedown', startMovingLeft);
leftButton.addEventListener('mouseup', stopMovingLeft);
leftButton.addEventListener('mouseleave', stopMovingLeft);
leftButton.addEventListener('touchstart', startMovingLeft);
leftButton.addEventListener('touchend', stopMovingLeft);
leftButton.addEventListener('touchcancel', stopMovingLeft);

rightButton.addEventListener('mousedown', startMovingRight);
rightButton.addEventListener('mouseup', stopMovingRight);
rightButton.addEventListener('mouseleave', stopMovingRight);
rightButton.addEventListener('touchstart', startMovingRight);
rightButton.addEventListener('touchend', stopMovingRight);
rightButton.addEventListener('touchcancel', stopMovingRight);


// Carga la imagen para los objetos y el jugador
const playerImage = new Image();
playerImage.src = '/static/images/objects/guardian.png'; // Ruta a la imagen del jugador

// Carga las imágenes para los objetos
const objectImages = [
    '/static/images/objects/airplane.png',
    '/static/images/objects/car.png',
    '/static/images/objects/dinosaur.png',
    '/static/images/objects/horse.png'
];

const loadedObjectImages = [];

objectImages.forEach(src => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
        loadedObjectImages.push(img);
    };
});

const urlParams = new URLSearchParams(window.location.search);
    let level = urlParams.get('level') || 'basic';

    console.log(level)



function startGame() {
    timeRemaining = 60; // Reinicia el tiempo al iniciar el juego
    // Ajustes basados en el nivel
    if (level === 'advanced') {
        timeRemaining = 45; // Tiempo menor para nivel avanzado
        objectSpeed = 4; // Aumenta la velocidad de los objetos
    }
    if (!isPaused) {
        score = 0;
        attentionObjects = [];
        feedback.textContent = '';
        clearInterval(gameInterval);
        clearInterval(timeInterval);
        gameInterval = setInterval(gameLoop, 1000 / 60);
        timeInterval = setInterval(updateTime, 1000); // Actualiza el tiempo cada segundo
    }
}


function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    updateObjects();
    drawObjects();
    drawPlayer();
    checkCollisions();
    if (timeRemaining <= 0) {
        endGame();
    }
}

function updateObjects() {
    if (isPaused) return;

    if (Math.random() < 0.02) {
        const randomImage = loadedObjectImages[Math.floor(Math.random() * loadedObjectImages.length)];
        attentionObjects.push({
            x: Math.random() * canvas.width,
            y: 0,
            width: 50,
            height: 50,
            image: randomImage
        });
    }
    attentionObjects.forEach(obj => {
        obj.y += objectSpeed;
    });
    attentionObjects = attentionObjects.filter(obj => obj.y < canvas.height);
}

function drawObjects() {
    attentionObjects.forEach(obj => {
        // Dibuja la imagen en lugar de un rectángulo
        ctx.drawImage(obj.image, obj.x, obj.y, obj.width, obj.height);
    });
}

function drawPlayer() {
    // Dibuja la imagen del jugador
    ctx.drawImage(playerImage, playerX, playerY, playerWidth, playerHeight);
}

function checkCollisions() {
    attentionObjects.forEach(obj => {
        if (
            obj.x < playerX + playerWidth &&
            obj.x + obj.width > playerX &&
            obj.y < playerY + playerHeight &&
            obj.y + obj.height > playerY
        ) {
            score++;
            feedback.textContent = `Pontuação: ${score}`;
            // Eliminar objeto después de colisión
            obj.y = canvas.height + 1;
        }
    });
}

function moveLeft() {
    playerX = Math.max(0, playerX - playerSpeed);
}

function moveRight() {
    playerX = Math.min(canvas.width - playerWidth, playerX + playerSpeed);
}

function startMovingLeft() {
    moveLeft();
    moveLeftInterval = setInterval(moveLeft, 1000 / 60);
}

function stopMovingLeft() {
    clearInterval(moveLeftInterval);
}

function startMovingRight() {
    moveRight();
    moveRightInterval = setInterval(moveRight, 1000 / 60);
}

function stopMovingRight() {
    clearInterval(moveRightInterval);
}

function updateTime() {
    if (isPaused) return;
    if (timeRemaining > 0) {
        timeRemaining--;
        timeDisplay.textContent = timeRemaining;
    }
    else {
        endGame();
    }
}
pauseButton.addEventListener('click', () => {
    isPaused = true;
    pauseButton.style.display = 'none';
    resumeButton.style.display = 'block';
});

resumeButton.addEventListener('click', () => {
    isPaused = false;
    pauseButton.style.display = 'block';
    resumeButton.style.display = 'none';
});
function endGame() {
    clearInterval(gameInterval);
    clearInterval(timeInterval);
    // alert("Tiempo terminado! Puntuación final: " + score);
    // window.location.href = '/results_atac?score=' + score;
    // Actualiza el contenido del span con el id 'scoreDisplay'
    $('#scoreDisplay').text(score);
    // Muestra el modal
    $('#timeUpModal').modal('show');            
    // Maneja el botón para redirigir a la página de resultados
    document.getElementById('goToResults').addEventListener('click', function() {
    window.location.href = '/results_atac?score=' + score;
    //feedback.textContent = `Juego terminado! Puntuación final: ${score}`;
    });
}
