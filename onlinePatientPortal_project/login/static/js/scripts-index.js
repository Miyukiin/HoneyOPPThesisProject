// Get all <li> elements of the navbar and their associated content sections
const menuItems = document.querySelectorAll('.navbar-menu li');
const contentSections = document.querySelectorAll('.content-section');

// Variable to lock clicks until the transition is complete. To avoid quick clicks for >2 items resulting in multiple shown overlapping section contents.
let isTransitioning = false;

// Function to hide all content sections
function hideAllContentSections() {
    contentSections.forEach(section => {
        if (section.classList.contains('active')) {
            // Start fade-out transition
            section.style.opacity = "0";

            // Use transitionend to wait until opacity transition is complete before setting display to none.
            section.addEventListener('transitionend', () => {
                section.style.display = "none"; // change to hide element.
                section.classList.remove('active'); // Remove 'active' class
            }, { once: true }); // Ensure this runs only once
        }

    });
}

// Add click event listeners to menu items
menuItems.forEach((item, index) => {  
    item.addEventListener('click', () => {
        // If a transition is already in progress, do nothing or if the clicked item is already active, do nothing
        console.log(isTransitioning);
        if (isTransitioning || (item.classList.contains('active')))  return;
    
        else {
            // Lock clicks to prevent quick successive clicks
            isTransitioning = true;
            hideAllContentSections(); // Hide all content sections first
            menuItems.forEach(i => i.classList.remove('active')); // Remove 'active' Class from all li items.
    
            // Show the clicked content section
            const activeSection = contentSections[index]; // Get the content-section of the clicked li item.
            item.classList.add('active'); // Add 'active' class to the clicked li item.

            activeSection.style.display = "block"; // Show content-section, which is still opacity 0, of clicked li item.

            requestAnimationFrame(() => {
                activeSection.style.opacity = "1"; // Fade-in transition of the content-section
            });

            // Unlock transitions and add active once fade-in ends
            activeSection.addEventListener('transitionend', () => {
                activeSection.classList.add('active');
                isTransitioning = false; // Unlock clicks after fade-in
            }, { once: true });
        }
    });
});
