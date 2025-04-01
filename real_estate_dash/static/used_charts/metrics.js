const animateNumber = (id, start, end, duration) => {
    const element = document.getElementById(id);
    if (!element) return; // Check if the element exists
    let startTime = null;

    const step = (timestamp) => {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        element.textContent = (progress * (end - start) + start).toFixed(2);
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    };

    requestAnimationFrame(step);
};

const fetchDataAndAnimate = async () => {
    try {
        const form = document.getElementById("filter-form");
        const formData = new FormData(form);
        const params = new URLSearchParams(formData).toString();

        const response = await fetch(`/api/apartment-stats/?${params}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();

        // Call animations
        animateNumber("price_per_sqm", 0, data.price_per_sqm, 700);
        animateNumber("avg_price", 0, data.avg_price, 700);
        animateNumber("price_per_sqm_usd", 0, data.price_per_sqm_usd, 700);
        animateNumber("avg_price_usd", 0, data.avg_price_usd, 700);
    } catch (error) {
        console.error("Error fetching data:", error);
        alert("Failed to fetch data. Please try again later.");
    }
};

const setupEventListeners = () => {
    // Add event listeners for all filters
    document.querySelectorAll(".filter, #from-date, #to-date").forEach((element) => {
        element.addEventListener("change", fetchDataAndAnimate);
    });

    // Add event listener for reset button
    const resetButton = document.getElementById("reset-button");
    if (resetButton) {
        resetButton.addEventListener("click", (event) => {
            event.preventDefault();
            document.getElementById("filter-form").reset();

            // Remove region and district inputs if they exist
            ["region", "district"].forEach((name) => {
                const input = document.querySelector(`input[name="${name}"]`);
                if (input) input.remove();
            });

            fetchDataAndAnimate();
        });
    }
};

// Initialize script
document.addEventListener("DOMContentLoaded", () => {
    fetchDataAndAnimate();
    setupEventListeners();
});
