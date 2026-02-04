(function () {
  function parseCodes(value) {
    return (value || "")
      .split(/[\n,]+/)
      .map(function (item) {
        return item.trim().toLowerCase();
      })
      .filter(function (item) {
        return item.length > 0;
      });
  }

  function isValidCode(code) {
    return /^[a-z0-9_-]+$/.test(code);
  }

  function mountTagInput(textarea) {
    if (!textarea || textarea.dataset.tagInputReady === "1") {
      return;
    }
    textarea.dataset.tagInputReady = "1";

    var chips = [];
    var editor = document.createElement("div");
    editor.className = "permission-tag-editor";

    var list = document.createElement("div");
    list.className = "permission-chip-list";

    var input = document.createElement("input");
    input.type = "text";
    input.className = "permission-chip-editor-input";
    input.placeholder = "Type code and press Enter or comma";

    editor.appendChild(list);
    editor.appendChild(input);
    textarea.classList.add("permission-chip-hidden");
    textarea.insertAdjacentElement("afterend", editor);

    function syncTextarea() {
      textarea.value = chips.join("\n");
    }

    function renderChips() {
      list.innerHTML = "";
      for (var i = 0; i < chips.length; i += 1) {
        (function (index) {
          var chip = document.createElement("span");
          chip.className = "permission-tag-chip";
          chip.textContent = chips[index];

          var removeBtn = document.createElement("button");
          removeBtn.type = "button";
          removeBtn.className = "permission-tag-remove";
          removeBtn.textContent = "×";
          removeBtn.setAttribute("aria-label", "Remove permission");
          removeBtn.addEventListener("click", function () {
            chips.splice(index, 1);
            renderChips();
            syncTextarea();
            input.focus();
          });

          chip.appendChild(removeBtn);
          list.appendChild(chip);
        })(i);
      }
    }

    function addCode(raw) {
      var code = (raw || "").trim().toLowerCase();
      if (!code || !isValidCode(code) || chips.indexOf(code) !== -1) {
        return;
      }
      chips.push(code);
    }

    function commitTypedCodes() {
      var values = parseCodes(input.value);
      for (var i = 0; i < values.length; i += 1) {
        addCode(values[i]);
      }
      input.value = "";
      renderChips();
      syncTextarea();
    }

    function loadInitial() {
      var values = parseCodes(textarea.value);
      for (var i = 0; i < values.length; i += 1) {
        addCode(values[i]);
      }
      renderChips();
      syncTextarea();
    }

    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        commitTypedCodes();
      } else if (event.key === "Backspace" && !input.value && chips.length) {
        chips.pop();
        renderChips();
        syncTextarea();
      }
    });

    input.addEventListener("blur", commitTypedCodes);

    var form = textarea.closest("form");
    if (form) {
      form.addEventListener("submit", commitTypedCodes);
    }

    loadInitial();
  }

  function initPermissionTagInput() {
    var fields = document.querySelectorAll("textarea.permissions-chip-input");
    for (var i = 0; i < fields.length; i += 1) {
      mountTagInput(fields[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPermissionTagInput);
  } else {
    initPermissionTagInput();
  }
})();
