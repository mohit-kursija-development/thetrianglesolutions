$(document).ready(function() {
  // Initialize the form validation
  $('#myForm').on('submit', function(event) {
    event.preventDefault(); // ✅ Always stop native form submission first
  
    if (!validateForm()) {
      return false; // No submission
    }

    $('#success').fadeIn();
  
    // Wait 3 seconds, then submit the form
    setTimeout(function() {
      console.log('Form submitted!');
      $('#myForm').off('submit'); // Remove this submit handler
      $('#myForm')[0].submit(); // ✅ Manual submission
    }, 2000);
  });
  
  // console.log('Document is ready!');
  const year = new Date().getFullYear();
  $('#year').text(year);

   // Autofill form fields
  //  $('#name').val('John Doe');
  //  $('#email').val('john.doe@example.com');
  //  $('#phone').val('9876543210');
  //  $('#service').val('webapp'); // Select from dropdown
  //  $('textarea[name="message"]').val('Hi! I need a web app for my business.');

   $('#allError').hide();
   $('#success').hide();
});
function validateForm() {
  const name = document.getElementById('name').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const email = document.getElementById('email').value.trim();
  const service = document.getElementById('service').value.trim();
  const message = document.getElementById('message').value.trim();

  const nameRegex = /^[A-Za-z\s]+$/;
  const phoneRegex = /^[0-9]+$/;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const allError = document.getElementById('allError');

  // Rather than alert use bootstrap modal or custom error message display
  if (!nameRegex.test(name) || name.length < 2) {
    allError.textContent = 'Name should only contain letters, spaces and greater than 2 characters.';
    allError.style.display = 'block'; // Show the error message
    return false;
  }
  if (!emailRegex.test(email)) {
    allError.textContent = 'Email is not valid.';
    allError.style.display = 'block'; // Show the error message
    return false;
  }

  if (!phoneRegex.test(phone) || phone.length !== 10) {
    allError.textContent = 'Phone number should be 10 digits long.';
    allError.style.display = 'block'; // Show the error message
    return false;
  }
  if (service === '') {
    allError.textContent = 'Please select a service.';
    allError.style.display = 'block'; // Show the error message
    return false;
  }
  // Check if message contains only letters, numbers, spaces, and punctuation
  const messageRegex = /^[A-Za-z0-9\s.,!?'"-]+$/;
  if (!messageRegex.test(message) || message.length < 10) {
    allError.textContent = 'Message should be at least 10 characters long and contain only letters, numbers, spaces, and punctuation.';
    allError.style.display = 'block'; // Show the error message
    return false;
  }
  // If all validations pass, hide the error message and allow form submission
  allError.style.display = 'none'; // Hide the error message
  allError.textContent = ''; // Clear the error message

  return true; 
}

