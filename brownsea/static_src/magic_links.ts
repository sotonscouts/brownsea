import Modal from 'bootstrap/js/dist/modal';

function getCsrfToken(form?: HTMLFormElement): string {
    const fromForm = form?.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value;
    if (fromForm) {
        return fromForm;
    }

    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

function postMagicLinkAction(url: string, form: HTMLFormElement): Promise<Response> {
    return fetch(url, {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(form),
        },
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const shareButton = document.querySelector<HTMLAnchorElement>('[data-magic-link-share]');
    const modalElement = document.getElementById('magic-link-modal');
    if (!shareButton || !modalElement) {
        return;
    }

    const modal = Modal.getOrCreateInstance(modalElement);
    const modalContent = document.getElementById('magic-link-modal-content');
    const panelUrl = shareButton.dataset.magicLinkPanelUrl;

    if (!modalContent || !panelUrl) {
        return;
    }

    shareButton.addEventListener('click', (event) => {
        event.preventDefault();
        fetch(panelUrl, {
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then((response) => response.text())
            .then((html) => {
                modalContent.innerHTML = html;
                modal.show();
            });
    });

    modalElement.addEventListener('submit', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLFormElement) || !target.dataset.magicLinkForm) {
            return;
        }

        event.preventDefault();

        postMagicLinkAction(target.action, target).then((response) => {
            if (target.dataset.magicLinkForm === 'create' && response.ok) {
                response.text().then((rowHtml) => {
                    document.getElementById('magic-link-empty')?.remove();
                    document.getElementById('magic-link-list')?.insertAdjacentHTML('afterbegin', rowHtml);
                    target.reset();
                });
                return;
            }

            if (target.dataset.magicLinkForm === 'revoke' && response.status === 204) {
                target.closest('[data-magic-link-row]')?.remove();
            }
        });
    });
});
