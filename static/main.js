var momoBody = document.getElementById("momo-body");
var currentDiv = null;
var inputLock = false;
var firstMsg = true;
var lastMsgTime = moment("1970-01-01 00:00:00","YYYY-MM-DD HH:mm:ss");

function downloadTxt(fileName, content) {
    let blob = new Blob([content], {
        type: "text/plain;charset=utf-8"
     });
    let reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onload = function(e) {
       let a = document.createElement('a');
       a.download = fileName;
       a.href = e.target.result;
       document.body.appendChild(a);
       a.click();
       document.body.removeChild(a);
   }
 } 

function addBanner(msg) {
    var newDiv = document.createElement('div');
    newDiv.className = "momo-banner";
    newDiv.innerHTML = msg;
    momoBody.appendChild(newDiv);
}

function addSensei(msg,stat) {
    if (msg == "") return;
    if (moment().diff(lastMsgTime,"minutes")>=10 && stat){
        addBanner(moment().locale('zh-cn').format("HH:mm"));
    }
    var messages = msg.split("\\");
    for (let j = 0; j < messages.length; j++) {
        var newDiv = document.createElement('div');
        newDiv.className = "momo-msg-sensei";
        newDiv.innerHTML = `
        <div class="momo-msg-sensei">
            <div class="momo-msg momo-msg-first" style="width: fit-content;">${messages[j]}</div>
        </div>
        `;
        momoBody.appendChild(newDiv);
    }
    momoBody.scrollTop = momoBody.scrollHeight;
    console.log(`sensei ${stat}:${msg}`);
    if (stat) {
        socket.emit('e', {'m': msg});
        inputLock = true;
        lastMsgTime = moment();
    }
}

function addStudent(msg) {
    if (firstMsg) {
        firstMsg = false;
        var newDiv = document.createElement("div");
        newDiv.className = "momo-msg-student";
        newDiv.innerHTML = `
            <div class="momo-avatar" style="background-image: url(static/head.webp); background-size: cover; background-position: center; background-repeat: no-repeat;"></div>
        `;
        var newMsgDiv = document.createElement("div");
        newMsgDiv.className = "momo-msg-main";
        newMsgDiv.innerHTML = `
            <div class="momo-name">未花</div>
            <div class="momo-msg momo-msg-first" style="width: fit-content;">${msg}</div>
        `;
        newDiv.appendChild(newMsgDiv);
        currentDiv = newMsgDiv;
        momoBody.appendChild(newDiv);
        console.log("student-first:"+msg);
    } else {
        currentDiv.innerHTML += `
                <div class="momo-msg" style="width: fit-content;">${msg}</div>
        `;
        console.log("student:"+msg);
    }
    momoBody.scrollTop = momoBody.scrollHeight;
}

var inputBar = document.getElementById("momo-input");
function processInput() {
    if (!inputLock) {
        var msg = inputBar.value;
        addSensei(msg,true);
        document.getElementById("momo-input").value = "";
    }
}

document.getElementById("momo-send").addEventListener("click", function() {
    processInput();
});

inputBar.addEventListener("keydown", function(e) {
    if (e.key == "Enter") {
        processInput();
    }
});

inputBar.addEventListener("focus", function() {
    momoBody.scrollTop = momoBody.scrollHeight;
});

document.getElementsByClassName("momo-header-cross")[0].addEventListener("click", function() {
    downloadTxt("chat.txt", momoBody.innerText);
});

var socket = io.connect(`${location.protocol}//${document.domain}:${location.port}/chat`);

socket.on('e', function(args) {
    console.log(args);
    if(args.s==0){
        console.log("start.");
        firstMsg = true;
        inputBar.placeholder = "Responding...";
    }else if(args.s==1){
        addStudent(args.r);
    }else if(args.s==2){
        addStudent(args.r);
        console.log("end.");
        inputBar.placeholder = "Type a message...";
        inputLock = false;
    }else if(args.s==3){
        firstMsg = true;
        addStudent(args.r);
        inputLock = false;
    }else if (args.s == 4) {
        alert(args.r); // 可选：提示用户页面即将刷新
        window.location.reload(); // 刷新页面
    }
});

moment.locale('en');

let xhr = new XMLHttpRequest();
xhr.open('GET', '/history', true);
xhr.onload = function() {
    let data = JSON.parse(xhr.responseText);
    addStudent("Sensei欢迎回来！");
    addStudent("我可是个乖乖看家的好孩子哦");
    for (let i = 0; i < data.length; i++) {
        if (data[i]["role"] == "assistant") {
            var messages = data[i]["content"].split("\\");
            firstMsg = true;
            for (let j = 0; j < messages.length; j++) {
                addStudent(messages[j]);
            }
        } else if (data[i]["role"] == "user") {
            addSensei(data[i]["content"],false);
        } else if (data[i]["role"] == "system") {
            var timeobj = moment(data[i]["content"].slice(9),"YYYY/MM/DD ddd HH:mm:ss");
            addBanner(timeobj.locale('zh-cn').format("HH:mm"));
            console.log(timeobj);
            lastMsgTime = timeobj;
        }
    }
};
xhr.send();
