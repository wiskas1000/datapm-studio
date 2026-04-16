/* datapm-studio — minimal JS, HTMX handles most interactivity */

/* ── Flash messages ── */
function flashMessage(category, text) {
    var container = document.getElementById('flash-container');
    if (!container) return;
    var div = document.createElement('div');
    div.className = 'flash flash-' + category;
    div.textContent = text;
    container.appendChild(div);
    setTimeout(function() { autoDismissFlash(div); }, 5000);
}

function autoDismissFlash(el) {
    if (!el || !el.parentNode) return;
    el.classList.add('flash-dismiss');
    setTimeout(function() {
        if (el.parentNode) el.parentNode.removeChild(el);
    }, 400);
}

document.addEventListener('DOMContentLoaded', function() {
    var existing = document.querySelectorAll('#flash-container .flash');
    existing.forEach(function(el) {
        setTimeout(function() { autoDismissFlash(el); }, 5000);
    });
});

/* ── HTMX error handling: surface failures as flash messages ── */
document.addEventListener('htmx:responseError', function(evt) {
    var status = evt.detail && evt.detail.xhr ? evt.detail.xhr.status : 0;
    flashMessage('error', 'Request failed (' + status + '). Please try again.');
});

document.addEventListener('htmx:sendError', function() {
    flashMessage('error', 'Network error. Check your connection and try again.');
});

document.addEventListener('htmx:timeout', function() {
    flashMessage('error', 'Request timed out. Please try again.');
});

/* ── Person dropdown selection ── */
function selectPerson(el) {
    var personId = el.getAttribute('data-person-id');
    var personName = el.getAttribute('data-person-name');
    var field = document.getElementById('requestor-field');
    if (!field) return;
    field.innerHTML =
        '<div class="selected-value">' +
            '<span>' + personName + '</span>' +
            '<input type="hidden" name="requestor_id" value="' + personId + '">' +
            '<button type="button" class="btn-clear" onclick="clearPerson()" title="Remove">&times;</button>' +
        '</div>';
}

function clearPerson() {
    var field = document.getElementById('requestor-field');
    if (!field) return;
    field.innerHTML =
        '<div class="search-input-wrap">' +
            '<input type="search" name="requestor_q" placeholder="Search people\u2026"' +
            ' hx-get="/persons/search" hx-trigger="keyup changed delay:300ms"' +
            ' hx-target="#requestor-results" hx-params="*"' +
            ' hx-vals=\'{"q": this.value}\' autocomplete="off">' +
            '<button type="button" class="btn-dropdown-toggle"' +
            ' hx-get="/persons/search?q="' +
            ' hx-target="#requestor-results"' +
            ' title="Show all">&#9662;</button>' +
            '<div id="requestor-results" class="dropdown-results"></div>' +
        '</div>';
    htmx.process(field);
}

/* ── Tag multi-select ── */
function selectTag(el) {
    var tagId = el.getAttribute('data-tag-id');
    var tagName = el.getAttribute('data-tag-name');
    var chips = document.getElementById('tag-chips');
    if (!chips) return;
    // Prevent duplicates
    if (chips.querySelector('[value="' + tagId + '"]')) return;
    var chip = document.createElement('span');
    chip.className = 'tag-chip';
    chip.innerHTML =
        tagName +
        '<input type="hidden" name="tag_ids" value="' + tagId + '">' +
        '<button type="button" class="btn-remove" onclick="this.parentElement.remove()">&times;</button>';
    chips.appendChild(chip);
}

function createAndSelectTag(name) {
    fetch('/tags/new-inline', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'name=' + encodeURIComponent(name)
    })
    .then(function(r) { return r.json(); })
    .then(function(tag) {
        var chips = document.getElementById('tag-chips');
        if (!chips) return;
        if (chips.querySelector('[value="' + tag.id + '"]')) return;
        var chip = document.createElement('span');
        chip.className = 'tag-chip';
        chip.innerHTML =
            tag.name +
            '<input type="hidden" name="tag_ids" value="' + tag.id + '">' +
            '<button type="button" class="btn-remove" onclick="this.parentElement.remove()">&times;</button>';
        chips.appendChild(chip);
        // Clear search input
        var input = document.querySelector('[name="tag_q"]');
        if (input) { input.value = ''; }
        var results = document.getElementById('tag-results');
        if (results) { results.innerHTML = ''; }
    });
}
