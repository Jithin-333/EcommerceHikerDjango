
// password eye icon view

document.querySelectorAll('.password-toggle-icon').forEach(togglePasswordIcon => {
  const passwordField = togglePasswordIcon.previousElementSibling;

  togglePasswordIcon.addEventListener('click', function () {
      if (passwordField.type === 'password') {
          passwordField.type = 'text';
          togglePasswordIcon.querySelector('i').classList.remove('fa-eye');
          togglePasswordIcon.querySelector('i').classList.add('fa-eye-slash');
      } else {
          passwordField.type = 'password';
          togglePasswordIcon.querySelector('i').classList.remove('fa-eye-slash');
          togglePasswordIcon.querySelector('i').classList.add('fa-eye');
      }
  });
});
 // Wait for the DOM to be fully loaded
 document.addEventListener("DOMContentLoaded", function() {
    // Set a timeout to remove the alert box after 5 seconds (5000 milliseconds)
    setTimeout(function() {
        var alertBox = document.getElementById("alertBox");
        if (alertBox) {
            alertBox.style.transition = "opacity 0.5s ease";
            alertBox.style.opacity = "0";
            setTimeout(function() {
                alertBox.remove();
            }, 500);  // Wait for the transition to complete before removing the element
        }
    }, 3000);
});

//password eye icon configuration starts here;---//



document.getElementById('phone').addEventListener('input', function() {
    var phoneInput = document.getElementById('phone');
    var phoneValue = phoneInput.value;
    var phonePattern = /^\d{10}$/;

    if (phonePattern.test(phoneValue)) {
        phoneInput.classList.remove('is-invalid');
        phoneInput.classList.add('is-valid');
    } else {
        phoneInput.classList.remove('is-valid');
        phoneInput.classList.add('is-invalid');
    }
});

//email validation
document.getElementById('email').addEventListener('input', function() {
    var emailInput = document.getElementById('email');
    var emailValue = emailInput.value;
    var emailPattern = /^[^\s@]+@gmail\.com$/;

    if (emailPattern.test(emailValue)) {
        emailInput.classList.remove('is-invalid');
        emailInput.classList.add('is-valid');
    } else {
        emailInput.classList.remove('is-valid');
        emailInput.classList.add('is-invalid');
    }
});

// USER_CART_SCRIPTS FOR QUANTITY

