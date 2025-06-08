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

function reverseGeocode(lat, lon, lang = "en") {
    // const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&accept-language=${lang}`;
    //
    // return fetch(url, {
    //     headers: {
    //         "User-Agent": "VoixApp/1.0 (your@email.com)"
    //     }
    // })
    //     .then(res => {
    //         if (!res.ok) throw new Error(`HTTP ${res.status}`);
    //         return res.json();
    //     })
    //     .then(data => {
    //         const {display_name, address} = data;
    //         const addr = address || {};
    //         const {city, village, country, town} = addr;
    //         return {
    //             city: city || town || village || "",
    //             country: country || "",
    //             display: display_name || ""
    //         };
    //     })
    //     .catch(err => {
    //         console.error("Reverse geocoding failed:", err);
    //         return {city: "", country: "", display: ""};
    //     });
    return Promise.resolve({
        city: `${lat}, ${lon}`,
        country: "France",
        display: `${lat}, ${lon}`
    });
}

export {getUserLocation, reverseGeocode};