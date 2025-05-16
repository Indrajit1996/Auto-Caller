// Optional: basic client-side validation
document.querySelector("form").addEventListener("submit", function(event) {
    const user = document.querySelector("input[name='username']").value;
    const pass = document.querySelector("input[name='password']").value;

    if (!user || !pass) {
        event.preventDefault();
        alert("Both username and password are required.");
    }
});
