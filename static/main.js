/*=============== DELETE CONFIRMATION ===============*/
function confirmDelete(event) {
    if (!confirm("Are you sure you want to delete this record?")) {
        event.preventDefault(); // Prevent the default action if user cancels
    }
}

/* Add event listeners to delete links */
const deleteLinks = document.querySelectorAll('.delete-link');
deleteLinks.forEach(link => {
    link.addEventListener('click', confirmDelete);
});

/*=============== FORM VALIDATION ===============*/
// Validate forms before submission
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', function(event) {
        let valid = true;
        
        // Validate all input fields
        form.querySelectorAll('input').forEach(input => {
            if (input.value.trim() === '') {
                valid = false;
                alert(input.name + " cannot be empty.");
            }
        });

        if (!valid) {
            event.preventDefault();
        }
    });
});
