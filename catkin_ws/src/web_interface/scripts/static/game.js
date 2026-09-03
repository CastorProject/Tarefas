document.addEventListener('DOMContentLoaded', () => {
    let time = 60; // Tiempo total en segundos
    let score = 0;
    let interval;
    let stimuliInterval;
    const gameArea = document.getElementById('game-area');
    const timeDisplay = document.getElementById('time');
    const scoreDisplay = document.getElementById('score');
    const startButton = document.getElementById('startButton');
    const pauseButton = document.getElementById('pauseButton');
    const resumeButton = document.getElementById('resumeButton');
    let isPaused = false;

    const try_again = 'sounds/tente_novamente.mp3'; // Usamos solo la ruta del archivo
    const categories = {
        'basic': {
            'animals': {
                names: ['dog', 'cat', 'rooster'],
                audio: {
                    'dog': 'sounds/animals/dog.mp3',
                    'cat': 'sounds/animals/cat.mp3',
                    'rooster': 'sounds/animals/rooster.mp3'
                },
                imagePath: '/static/images/animals/'
            },
            'vowels': {
                names: ['a', 'e', 'i', 'o', 'u'],
                audio: {
                    'a': 'sounds/vowels/a.mp3',
                    'e': 'sounds/vowels/e.mp3',
                    'i': 'sounds/vowels/i.mp3',
                    'o': 'sounds/vowels/o.mp3',
                    'u': 'sounds/vowels/u.mp3'
                },
                imagePath: '/static/images/vowels/'
            },
            'colors': {
                names: ['red', 'blue', 'yellow'],
                audio: {
                    'red': 'sounds/colors/red.mp3',
                    'blue': 'sounds/colors/blue.mp3',
                    'yellow': 'sounds/colors/yellow.mp3'
                },
                imagePath: '/static/images/colors/'
            }
        },
        'advanced': {
            'instruments': {
                names: ['drum', 'guitar', 'maracas', 'trumpet'],
                audio: {
                    'drum': 'sounds/instruments/drum.mp3',
                    'guitar': 'sounds/instruments/guitar.mp3',
                    'maracas': 'sounds/instruments/maracas.mp3',
                    'trumpet': 'sounds/instruments/trumpet.mp3'
                },
                imagePath: '/static/images/instruments/'
            },
            'figures': {
                names: ['circle', 'kite', 'square', 'triangle'], 
                audio: {
                    'circle': 'sounds/figures/circle.mp3',
                    'kite': 'sounds/figures/kite.mp3',
                    'square': 'sounds/figures/square.mp3',
                    'triangle': 'sounds/figures/triangle.mp3'
                },
                imagePath: '/static/images/figures/'
            },
            'activities': {
                names: ['eating', 'laugh', 'silence', 'whistle'],
                audio: {
                    'eating': 'sounds/activities/eating.mp3',
                    'laugh': 'sounds/activities/laugh.mp3',
                    'silence': 'sounds/activities/silence.mp3',
                    'whistle': 'sounds/activities/whistle.mp3'
                },
                imagePath: '/static/images/activities/'
            }
        }
    };

    let currentCategory = 'animals'; // Puedes inicializar en 'animals' o en 'vowels'

    const urlParams = new URLSearchParams(window.location.search);
    let level = urlParams.get('level') || 'basic';

    const imageWidth = 90; // Tamaño de las imágenes
    const imageHeight = 90;
    const minSpacing = 70; // Espacio mínimo entre imágenes

    let occupiedMap = [];
    // Función para enviar el archivo de audio al robot a través de Flask
    function sendAudioToRobot(audioFile) {
        // Convierte la ruta al formato que el robot espera (ejemplo: static/sounds -> animals/dog)
        //const robotAudioFile = audioFile.replace('/static/', '');
        robotAudioFile = audioFile
        console.log('Enviando audio al robot:', robotAudioFile) //Debugging

        fetch('/play_audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ audio: robotAudioFile }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Audio enviado al robot:', data);
        })
        .catch((error) => {
            console.error('Error al enviar el audio al robot:', error);
        });
    }

    function startGame() {
        // Ajustes basados en el nivel
        if (level === 'advanced') {
            time = 45; // Tiempo menor para nivel avanzado
            currentCategory = 'instruments';
        }

        timeDisplay.innerText = time;

        interval = setInterval(() => {
            if (!isPaused) { // Solo actualizar si no está pausado
                if (time <= 0) {
                    clearInterval(interval);
                    clearInterval(stimuliInterval);
                    $('#scoreDisplay').text(score);
                    $('#timeUpModal').modal('show');
                    
                    document.getElementById('goToResults').addEventListener('click', function() {
                        window.location.href = '/results_atac?score=' + score;
                });
                } else {
                    time--;
                    timeDisplay.innerText = time;
                }
            }
        }, 1000);
        createStimuli();
        stimuliInterval = setInterval(() =>{
            if (!isPaused){
                createStimuli()
            }
        }, 5000);
    }

    function initializeOccupiedMap() {
        const cols = Math.ceil(gameArea.clientWidth / (imageWidth + minSpacing));
        const rows = Math.ceil(gameArea.clientHeight / (imageHeight + minSpacing));
        occupiedMap = Array.from({ length: rows }, () => Array(cols).fill(false));
    }

    function markOccupied(x, y) {
        const colStart = Math.floor(x / (imageWidth + minSpacing));
        const colEnd = Math.floor((x + imageWidth) / (imageWidth + minSpacing));
        const rowStart = Math.floor(y / (imageHeight + minSpacing));
        const rowEnd = Math.floor((y + imageHeight) / (imageHeight + minSpacing));
        
        for (let row = rowStart; row <= rowEnd; row++) {
            for (let col = colStart; col <= colEnd; col++) {
                if (col >= 0 && col < occupiedMap[0].length && row >= 0 && row < occupiedMap.length) {
                    occupiedMap[row][col] = true;
                }
            }
        }
    }

    function isOccupied(x, y) {
        const colStart = Math.floor(x / (imageWidth + minSpacing));
        const colEnd = Math.floor((x + imageWidth) / (imageWidth + minSpacing));
        const rowStart = Math.floor(y / (imageHeight + minSpacing));
        const rowEnd = Math.floor((y + imageHeight) / (imageHeight + minSpacing));

        for (let row = rowStart; row <= rowEnd; row++) {
            for (let col = colStart; col <= colEnd; col++) {
                if (col >= 0 && col < occupiedMap[0].length && row >= 0 && row < occupiedMap.length) {
                    if (occupiedMap[row][col]) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    function getRandomPosition() {
        const maxX = gameArea.clientWidth - imageWidth;
        const maxY = gameArea.clientHeight - imageHeight;
        const randomX = Math.floor(Math.random() * maxX);
        const randomY = Math.floor(Math.random() * maxY);
        return { x: randomX, y: randomY };
    }

    function createStimuli() {

        if (isPaused) return;

        gameArea.innerHTML = ''; // Limpiar los estímulos anteriores
        initializeOccupiedMap(); // Reiniciar el mapa de ocupación

        const category = categories[level][currentCategory];
        if (!category) {
            console.error("Categoría no encontrada:", currentCategory);
            return;
        }

        const chosenItem = category.names[Math.floor(Math.random() * category.names.length)];
        
        // Depuración para verificar si el audio se envía correctamente
        console.log("Archivo de audio elegido:", category.audio[chosenItem]);

        // Enviar el audio al robot
        sendAudioToRobot(category.audio[chosenItem]);

        // Mezclar el orden de las imágenes
        const shuffledItems = category.names.sort(() => Math.random() - 0.5);

        shuffledItems.forEach((item) => {
            const stimulus = document.createElement('img');
            stimulus.classList.add('stimulus');
            stimulus.src = category.imagePath + item + '.png';
            stimulus.alt = item;

            let position;
            let attempts = 0;
            const maxAttempts = 200; // Máximo número de intentos para encontrar una posición válida

            do {
                position = getRandomPosition();
                attempts++;
                if (attempts > maxAttempts) {
                    console.error("No se pudo encontrar una posición válida para el estímulo:", item);
                    return;
                }
            } while (isOccupied(position.x, position.y));

            // Marcar la posición como ocupada
            markOccupied(position.x, position.y);

            stimulus.style.position = 'absolute';
            stimulus.style.left = position.x + 'px';
            stimulus.style.top = position.y + 'px';
            stimulus.style.width = imageWidth + 'px';
            stimulus.style.height = imageHeight + 'px';
            stimulus.style.cursor = 'pointer';

            const handleStimulusClick = () => {
                if (isPaused) return;
                if (stimulus.alt === chosenItem) {
                    score++;
                    scoreDisplay.innerText = score;
                    gameArea.innerHTML = ''; // Limpiar los estímulos después de seleccionar correctamente
                }
                else {
                    sendAudioToRobot(try_again); // Reproducir audio de "intenta nuevamente" en el robot
                }
            };

            stimulus.addEventListener('click', handleStimulusClick);
            stimulus.addEventListener('touchstart', handleStimulusClick);

            gameArea.appendChild(stimulus);
        });

        if (level === 'advanced') {
            currentCategory = currentCategory === 'instruments' ? 'figures' : (currentCategory === 'figures' ? 'activities' : 'instruments');
        } else {
            currentCategory = currentCategory === 'animals' ? 'vowels' : (currentCategory === 'vowels' ? 'colors' : 'animals');
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

    startButton.addEventListener('click', startGame);
});
