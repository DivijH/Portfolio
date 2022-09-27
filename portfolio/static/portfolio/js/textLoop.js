var words = ['Machine Learning', 'Web Development', 'Game Development', '3D Modeling']
var part;
var i = 0;
var offset = 0;
var len = words.length;
var forwards = true;
var skip_count = 0;
var skip_delay = 15;
var speed = 70;

var wordflick = function() {
    setInterval(function() {
        if(forwards) {
            if(offset >= words[i].length) {
                ++skip_count;
                if(skip_count == skip_delay) {
                    forwards = false;
                    skip_count = 0;
                }
            }
        } else {
            if(offset == 0) {
                forwards = true;
                i++;
                if(i >= len) {
                    i=0;
                }
            }
        }
        part = words[i].substring(0, offset);
        if(skip_count == 0) {
            if(forwards) {
                offset++;
            } else {
                offset--;
            }
        }
        console.log('HERE', part, i, offset);
        document.getElementsByClassName('word')[0].innerHTML = part;
    }, speed);
};

wordflick();