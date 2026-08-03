/**
 * Sync Ending account ID with Starting ID for single-account reports.
 * User can set a different Ending ID for an account range.
 */
const AccountRangeSync = (() => {
    let linked = true;

    function syncEndFromStart(endTitle) {
        if (!linked) return;
        const startEl = document.getElementById('start_ac_id');
        const endEl = document.getElementById('end_ac_id');
        const endTitleEl = document.getElementById('end_ac_title');
        if (!startEl || !endEl) return;
        endEl.value = startEl.value;
        if (!endTitleEl) return;
        if (endTitle !== undefined) {
            endTitleEl.textContent = endTitle;
            return;
        }
        const startTitleEl = document.getElementById('start_ac_title');
        if (startTitleEl) endTitleEl.textContent = startTitleEl.textContent;
    }

    function updateLinkedState() {
        const start = document.getElementById('start_ac_id')?.value.trim() || '';
        const end = document.getElementById('end_ac_id')?.value.trim() || '';
        linked = !end || end === start;
    }

    async function onStartChange(validateFn) {
        syncEndFromStart();
        if (typeof validateFn !== 'function') return;
        await validateFn('start');
        if (linked) await validateFn('end');
    }

    async function onEndChange(validateFn) {
        updateLinkedState();
        if (typeof validateFn === 'function') await validateFn('end');
    }

    function pickAccount(target, acId, acTitle, validateFn) {
        document.getElementById(`${target}_ac_id`).value = acId;
        document.getElementById(`${target}_ac_title`).textContent = acTitle;
        if (target === 'start') {
            if (linked) {
                document.getElementById('end_ac_id').value = acId;
                document.getElementById('end_ac_title').textContent = acTitle;
                if (typeof validateFn === 'function') {
                    validateFn('start');
                    validateFn('end');
                }
            } else if (typeof validateFn === 'function') {
                validateFn('start');
            }
            return;
        }
        updateLinkedState();
        if (typeof validateFn === 'function') validateFn('end');
    }

    function reset() {
        linked = true;
    }

    function bind(validateFn) {
        const startEl = document.getElementById('start_ac_id');
        const endEl = document.getElementById('end_ac_id');
        if (!startEl || !endEl) return;

        const handleStart = () => onStartChange(validateFn);
        const handleEnd = () => onEndChange(validateFn);
        startEl.addEventListener('input', handleStart);
        startEl.addEventListener('change', handleStart);
        endEl.addEventListener('input', handleEnd);
        endEl.addEventListener('change', handleEnd);
    }

    return { bind, reset, pickAccount };
})();
