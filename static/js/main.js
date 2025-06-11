import {getUserLocation} from "./utils.js";

const userLang = window.APP_CONFIG.userLang;
const categoryMap = {};

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    fetchCategories();
    fetchReports();
    fetchUserActivity();

    document.getElementById("submit-report").addEventListener("click", submitNewReport);

    const countInput = document.getElementById("count-filter");

    countInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") fetchReports();
    });

    countInput.addEventListener("blur", fetchReports);

});

function fetchCategories() {
    fetch("/api/categories/")
        .then(res => res.json())
        .then(data => {
            const selectAll = document.getElementById("category-filter");
            selectAll.innerHTML = `<option value="">All</option>`;

            const {categories} = data;
            categories.forEach(cat => {
                const {name_fr, name_en} = cat;
                categoryMap[name_en] = cat;

                const opt = document.createElement("option");
                opt.value = name_en;
                opt.textContent = userLang === "fr" ? name_fr : name_en;
                selectAll.appendChild(opt);
            });
        })
        .catch(err => {
            console.error("Failed to fetch categories:", err);
        });

    document.getElementById("category-filter").addEventListener("change", fetchReports);
}


function setupNavigation() {
    const validPages = ["page-all", "page-my", "page-new"];

    document.querySelectorAll("nav button").forEach(btn => {
        const targetPage = btn.getAttribute("data-page");

        if (validPages.includes(targetPage)) {
            btn.addEventListener("click", () => switchPage(targetPage));
        } else {
            console.warn(`Unknown target page: "${targetPage}"`);
        }
    });
}


const pageIds = ["page-all", "page-my", "page-new"];

function switchPage(activeId) {
    pageIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) {
            console.warn(`Missing page element: ${id}`);
            return;
        }
        el.style.display = (id === activeId) ? "block" : "none";
    });
}

function fetchReports() {
    const container = document.getElementById("reports");
    const category = document.getElementById("category-filter").value;
    let count = parseInt(document.getElementById("count-filter").value, 10);
    if (isNaN(count) || count < 10) count = 10;

    const url = category
        ? `/api/reports/by_category/?category_name=${encodeURIComponent(category)}&n=${count}`
        : `/api/reports/?n=${count}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            const {reports: reports1} = data;
            const reports = reports1 || data;
            container.innerHTML = "";
            reports.forEach(r => renderReport(r, container));
        })
        .catch(err => {
            console.error("Failed to fetch:", err);
        });
}


function fetchUserActivity() {
    loadSection("/api/reports/user/", "my-reports");
    loadSection("/api/reports/user/voted/", "my-votes");
    loadSection("/api/reports/user/commented/", "my-comments");
}

function loadSection(url, containerId) {
    fetch(url)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById(containerId);
            container.innerHTML = "";
            const {reports} = data;
            (reports || []).forEach(r => renderReport(r, container));
        })
        .catch(err => {
            console.error("Failed to fetch:", err);
        });
}

function renderReport(report, container) {
    const div = document.createElement("div");

    const {
        id,
        title,
        description,
        vote_count,
        status,
        image_url,
        category,
        user_name,
        user_email,
        created_at,
        zipcode,
        province,
        place
    } = report;

    // Title
    const titleEl = document.createElement("h3");
    titleEl.textContent = title;
    div.appendChild(titleEl);

    // Description
    const desc = document.createElement("p");
    desc.textContent = description;
    div.appendChild(desc);

    // Category - with localized description
    if (category) {
        const catData = categoryMap[category];
        if (catData) {
            const catEl = document.createElement("p");
            const {description_en, description_fr, name_en, name_fr} = catData;
            const name = userLang === "fr" ? name_fr : name_en;
            const desc = userLang === "fr" ? description_fr : description_en;
            catEl.innerHTML = `<strong>Category:</strong> ${name}<br><em>${desc}</em>`;
            div.appendChild(catEl);
        }
    }

    // Status
    const statusEl = document.createElement("p");
    statusEl.innerHTML = `<strong>Status:</strong> ${status}`;
    div.appendChild(statusEl);

    // Image
    if (image_url) {
        const img = document.createElement("img");
        img.src = image_url;
        img.alt = "Report Image";
        img.style.maxWidth = "300px";
        div.appendChild(img);
    }

    // Metadata
    const meta = document.createElement("p");
    meta.innerHTML = `<strong>Reported by:</strong> ${user_name || "Anonymous"} (${user_email || "N/A"})<br><strong>Created at:</strong> ${new Date(created_at).toLocaleString()}`;
    div.appendChild(meta);

    // Votes
    const votes = document.createElement("p");
    votes.innerHTML = `Votes: <span id="votes-${id}">${vote_count || 0}</span>`;
    div.appendChild(votes);

    const voteBtn = document.createElement("button");
    voteBtn.textContent = "Vote";
    voteBtn.addEventListener("click", () => {
        fetch("/api/votes/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({report_id: id})
        }).then(() => updateVoteCount(id))
            .catch(err => console.error("Failed to vote:", err));
    });
    div.appendChild(voteBtn);

    // City Code
    const locEl = document.createElement("p");
    if (zipcode.length === 0 || zipcode === "/") {
        locEl.textContent = `📍 ${userLang === "fr" ? "outre-mer" : "overseas"}`;
    } else {
        locEl.textContent = `📍 ${place}[${zipcode}], ${province}`;
    }

    div.appendChild(locEl);


    // Comment
    const textarea = document.createElement("textarea");
    textarea.placeholder = "Write a comment...";
    div.appendChild(textarea);

    const commentBtn = document.createElement("button");
    commentBtn.textContent = "Submit Comment";
    commentBtn.addEventListener("click", () => {
        const content = textarea.value.trim();
        if (!content) return;
        fetch(`/api/reports/${id}/comments/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({content})
        }).then(() => {
            textarea.value = "";
            loadComments(id);
        }).catch(err => console.error("Failed to comment:", err));
    });
    div.appendChild(commentBtn);

    const commentsDiv = document.createElement("div");
    commentsDiv.id = `comments-${id}`;
    div.appendChild(commentsDiv);

    container.appendChild(div);
    container.appendChild(document.createElement("hr"));

    loadComments(id);
}


function updateVoteCount(reportId) {
    fetch(`/api/reports/${reportId}/votes/`)
        .then(res => res.json())
        .then(data => {
            const el = document.getElementById(`votes-${reportId}`);
            if (el) {
                const {vote_count} = data;
                el.textContent = vote_count;
            }
        })
        .catch(err => {
            console.error("Failed to fetch:", err);
        });
}

function loadComments(reportId) {
    fetch(`/api/reports/${reportId}/comments/`)
        .then(res => res.json())
        .then(data => {
            const {comments} = data;
            renderComments(reportId, comments);
        })
        .catch(err => {
            console.error("Failed to fetch:", err);
        });
}

function renderComments(reportId, comments) {
    const container = document.getElementById(`comments-${reportId}`);
    container.innerHTML = "";

    const previewCount = 4;
    const visible = comments.slice(0, previewCount);
    const hidden = comments.slice(previewCount);

    visible.forEach(c => container.appendChild(createCommentElement(c)));

    const hiddenDiv = document.createElement("div");
    hiddenDiv.style.display = "none";
    hidden.forEach(c => hiddenDiv.appendChild(createCommentElement(c)));
    container.appendChild(hiddenDiv);

    if (hidden.length > 0) {
        const toggle = document.createElement("button");
        toggle.textContent = "Show all comments";
        toggle.addEventListener("click", () => {
            const expanded = hiddenDiv.style.display === "block";
            hiddenDiv.style.display = expanded ? "none" : "block";
            toggle.textContent = expanded ? "Show all comments" : "Hide extra comments";
        });
        container.appendChild(toggle);
    }
}

function createCommentElement(c) {
    const p = document.createElement("p");
    const {username, is_admin, content} = c;
    p.className = is_admin ? "admin-comment" : "user-comment";
    p.textContent = `User ${username}: ${content}`;
    return p;
}



function submitNewReport() {
    const title = document.getElementById("new-title").value.trim();
    const description = document.getElementById("new-description").value.trim();
    const image = document.getElementById("new-image").files[0];
    const resultEl = document.getElementById("submit-result");
    resultEl.textContent = "";  // 清空旧信息

    if (!title || !description) {
        resultEl.textContent = "Please fill in both title and description.";
        return;
    }

    const allowedTypes = ["image/jpeg", "image/png"];
    const maxSize = 2 * 1024 * 1024; // 2MB

    if (image) {
        if (!allowedTypes.includes(image.type)) {
            resultEl.textContent = "❌ Only JPG and PNG images are allowed.";
            return;
        }
        if (image.size > maxSize) {
            resultEl.textContent = "❌ Image must be smaller than 2MB.";
            return;
        }
    }

    getUserLocation()
        .then(({latitude, longitude}) => {
            const data = {title, description, latitude, longitude};
            console.log(data);
            const formData = new FormData();
            formData.append("data", JSON.stringify(data));
            if (image) formData.append("image", image);

            return fetch("/api/reports/", {
                method: "POST",
                body: formData
            });
        })
        .then(async res => {
            let result;
            try {
                result = await res.json();
            } catch {
                result = {error: "Invalid response from server."};
            }

            if (res.ok && result.id) {
                resultEl.textContent = "✅ Report submitted successfully!";
            } else {
                resultEl.textContent = `❌ Error: ${result.error || "Submission failed."}`;
            }
        })
        .catch(err => {
            resultEl.textContent = `❌ Network error: ${err}`;
        });
}
