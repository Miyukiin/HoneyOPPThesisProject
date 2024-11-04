// Get all <li> elements of the navbar and their associated content sections
const menuItems = document.querySelectorAll('.navbar-menu li');
const contentSections = document.querySelectorAll('.content-section');

// Variable to lock clicks until the transition is complete. To avoid quick clicks for >2 items resulting in multiple shown overlapping section contents.
let isTransitioning = false;

// Function to hide all content sections
function hideAllContentSections() {
    contentSections.forEach(section => {
        if (section.classList.contains('active')) {
            // Add 'active' class to section-content and start transition to opacity 0 (As specified in CSS).
            section.classList.remove('active'); 
            // Use a timeout matching the CSS transition duration to prevent quick clicks issue
            setTimeout(() => {
                isTransitioning = false; // Unlock clicks
            }, 500); // Correspond to CSS transition duration
        }
    });
}


// Add click event listeners to menu items
menuItems.forEach((item, index) => {  
    item.addEventListener('click', () => {
        // If a transition is already in progress, do nothing or if the clicked item is already active, do nothing
        if (isTransitioning || (item.classList.contains('active')))  return;
    
        else {
            // Lock clicks to prevent quick successive clicks
            isTransitioning = true;
            hideAllContentSections(); // Hide all content sections first
            menuItems.forEach(i => i.classList.remove('active')); // Remove 'active' Class from all li items.
    
            // Show the clicked content section
            const activeSection = contentSections[index]; // Get the content-section of the clicked li item.
            item.classList.add('active'); // Add 'active' class to the clicked li item.
            
            setTimeout(() => {
                // Add 'active' class to section-content and start transition to opacity 1 (As specified in CSS).
                activeSection.classList.add('active'); 
            }, 500); // Correspond to CSS transition duration
        }
    });
});
