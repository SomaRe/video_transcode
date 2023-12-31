// script.js

document.addEventListener("DOMContentLoaded", function() {
    const videoElement = document.getElementById("streamed-video");
    const videoUrl = "/stream_video"; // The URL of your Flask streaming endpoint

    if (videoElement.canPlayType) {
        const mimeCodec = 'video/mp4';
        if (videoElement.canPlayType(mimeCodec) !== "") {
            videoElement.src = videoUrl;
        } else {
            console.error("Your browser does not support the required video codec.");
        }
    }

    videoElement.addEventListener("error", function(e) {
        console.error("An error occurred while loading the video.");
        console.error(e);
    });
});
