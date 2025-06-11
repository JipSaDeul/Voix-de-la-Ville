// utils.js

/**
 * Function to get the user's current latitude and longitude.
 *
 * @returns {Promise} A promise that resolves to an object containing latitude and longitude on success,
 *                    or rejects with an error message on failure.
 */
function getUserLocation() {
    return new Promise((resolve, reject) => {
        // Check if the browser supports Geolocation API
        if (!navigator.geolocation) {
            reject("Geolocation is not supported by this browser.");  // Reject if Geolocation is not supported
            return;
        }

        // Get the current position of the user
        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Extract latitude and longitude from the position object
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                resolve({latitude, longitude});  // Resolve the promise with latitude and longitude
            },
            (error) => {
                reject(`Error getting location: ${error.message}`);  // Reject with an error message if failed
            }
        );
    });
}

export {getUserLocation};