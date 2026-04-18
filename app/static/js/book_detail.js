document.addEventListener("DOMContentLoaded", function () {
    const slider = document.getElementById('draggable-slider');
    if (!slider) return;

    let isDown = false;
    let startX;
    let scrollLeft;
    let autoScrollInterval;

    function startAutoScroll() {
        autoScrollInterval = setInterval(() => {
            if (!isDown) {
                slider.scrollLeft += 1; // Tốc độ trượt
                // Trượt vô hạn. Nếu cuộn tới cuối, quay lại 0
                if (slider.scrollLeft >= (slider.scrollWidth - slider.clientWidth - 1)) {
                    slider.scrollLeft = 0;
                }
            }
        }, 20); // 20ms mỗi khung hình
    }

    function stopAutoScroll() {
        clearInterval(autoScrollInterval);
    }

    slider.addEventListener('mousedown', (e) => {
        isDown = true;
        slider.style.cursor = 'grabbing';
        startX = e.pageX - slider.offsetLeft;
        scrollLeft = slider.scrollLeft;
        stopAutoScroll();
    });

    slider.addEventListener('mouseleave', () => {
        isDown = false;
        slider.style.cursor = 'grab';
        startAutoScroll();
    });

    slider.addEventListener('mouseup', () => {
        isDown = false;
        slider.style.cursor = 'grab';
        startAutoScroll();
    });

    slider.addEventListener('mouseenter', () => {
        stopAutoScroll();
    });

    slider.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX) * 2; // Tốc độ rê 2
        slider.scrollLeft = scrollLeft - walk;
    });

    // Bắt đầu trượt tự động khi load trang
    startAutoScroll();
});

document.addEventListener("DOMContentLoaded", function () {
    // Logic cho Modal Phóng To Ảnh
    const modal = document.getElementById("image-modal");
    const bookCover = document.getElementById("main-book-cover");
    const modalImg = document.getElementById("zoomed-image");
    const closeBtn = document.querySelector(".close-modal");

    if (bookCover && modal) {
        bookCover.addEventListener("click", function () {
            modal.style.display = "block";
            modalImg.src = this.src;
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", function () {
            modal.style.display = "none";
        });
    }

    // Đóng khi click bên ngoài ảnh
    if (modal) {
        modal.addEventListener("click", function (e) {
            if (e.target !== modalImg) {
                modal.style.display = "none";
            }
        });
    }
});
