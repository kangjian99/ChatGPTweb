let loading = document.getElementById('loading');
let form = document.querySelector('form');
form.addEventListener('submit', () => {
    loading.style.display = 'block';
});

function copyToClipboard() {
  var resText = document.getElementById("res").innerText;
  navigator.clipboard.writeText(resText).then(function() {
    var animation = document.getElementById("copy-animation");
    animation.classList.remove("hide");
    setTimeout(function() {
      animation.classList.add("hide");
    }, 3000);  // 3 秒后隐藏提示框
  });
}

var dropdown = document.getElementById("dropdown");
var pid = dropdown.getAttribute("data-pid");
var pid_list = pid.split(",");
for (var i = 1; i <= pid_list.length; i++) {
  var option = document.createElement("option");
  option.text = pid_list[i-1];
  option.value = i;
  dropdown.add(option);
}