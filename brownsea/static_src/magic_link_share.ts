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

class MagicLinkShare extends HTMLElement {
    private modal: Modal | null = null;
    private readonly modalId: string;
    private readonly modalContentId: string;

    constructor() {
        super();
        const suffix = Math.random().toString(36).slice(2, 9);
        this.modalId = `magic-link-modal-${suffix}`;
        this.modalContentId = `magic-link-modal-content-${suffix}`;
    }

    connectedCallback(): void {
        const panelUrl = this.getAttribute('panel-url');
        if (!panelUrl) {
            console.error('magic-link-share requires a panel-url attribute');
            return;
        }

        this.render();

        const button = this.querySelector<HTMLButtonElement>('[data-magic-link-open]');
        const modalElement = this.querySelector<HTMLElement>(`#${this.modalId}`);
        const modalContent = this.querySelector<HTMLElement>(`#${this.modalContentId}`);

        if (!button || !modalElement || !modalContent) {
            return;
        }

        this.modal = Modal.getOrCreateInstance(modalElement);

        button.addEventListener('click', () => {
            fetch(panelUrl, {
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then((response) => response.text())
                .then((html) => {
                    modalContent.innerHTML = html;
                    modalElement.setAttribute('aria-labelledby', 'magic-link-modal-label');
                    this.modal?.show();
                });
        });

        modalElement.addEventListener('show.bs.modal', () => {
            button.setAttribute('aria-expanded', 'true');
        });

        modalElement.addEventListener('hidden.bs.modal', () => {
            button.setAttribute('aria-expanded', 'false');
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
                        modalContent.querySelector('#magic-link-empty')?.remove();
                        modalContent.querySelector('#magic-link-list')?.insertAdjacentHTML('afterbegin', rowHtml);
                        target.reset();
                    });
                    return;
                }

                if (target.dataset.magicLinkForm === 'revoke' && response.status === 204) {
                    target.closest('[data-magic-link-row]')?.remove();
                }
            });
        });
    }

    disconnectedCallback(): void {
        this.modal?.dispose();
        this.modal = null;
    }

    private render(): void {
        this.innerHTML = `
            <button
                type="button"
                class="share-link"
                data-magic-link-open
                aria-haspopup="dialog"
                aria-controls="${this.modalId}"
                aria-expanded="false"
            >
                <i class="bi bi-share" aria-hidden="true"></i>Share
            </button>
            <div
                class="modal fade"
                id="${this.modalId}"
                tabindex="-1"
                aria-label="Share magic links"
                aria-hidden="true"
            >
                <div class="modal-dialog modal-lg">
                    <div class="modal-content" id="${this.modalContentId}">
                        <div class="modal-body text-center py-5">
                            <div class="spinner-border" role="status">
                                <span class="visually-hidden">Loading…</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

if (!customElements.get('magic-link-share')) {
    customElements.define('magic-link-share', MagicLinkShare);
}

export default MagicLinkShare;
