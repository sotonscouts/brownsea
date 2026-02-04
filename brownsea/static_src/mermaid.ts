// Type definitions for Mermaid
interface MermaidConfig {
    startOnLoad: boolean;
    theme: string;
    themeVariables: Record<string, string>;
}

interface MermaidAPI {
    initialize: (config: MermaidConfig) => void;
    run?: (options?: { suppressErrors?: boolean }) => Promise<void>;
    contentLoaded?: () => void;
    render?: (id: string, text: string) => Promise<{ svg: string }>;
}

interface WindowWithMermaid extends Window {
    mermaid?: MermaidAPI;
}

class MermaidInitialiser {
    private static instance: MermaidInitialiser | null = null;
    private loading = false;
    private initialised = false;
    private mutationObserver: MutationObserver | null = null;
    private modalListenersSetup = false;
    private mermaidAPI: MermaidAPI | null = null;
    private readonly MAX_RETRY_ATTEMPTS = 3;
    private readonly RETRY_DELAY_MS = 500;
    private readonly processedDiagrams = new Set<HTMLElement>();

    static getInstance(): MermaidInitialiser {
        if (!MermaidInitialiser.instance) {
            MermaidInitialiser.instance = new MermaidInitialiser();
        }
        return MermaidInitialiser.instance;
    }

    /**
     * Get CSS variable value from Bootstrap theme with fallbacks
     */
    private getCSSVariable(bootstrapVar: string, customVar: string | null, fallback: string): string {
        const root = document.documentElement;
        const styles = getComputedStyle(root);

        // Try Bootstrap CSS variable first (e.g., --bs-primary)
        const bsValue = styles.getPropertyValue(`--bs-${bootstrapVar}`).trim();
        if (bsValue) {
            return bsValue;
        }

        // Try custom CSS variable if provided (e.g., --scout-purple)
        if (customVar) {
            const customValue = styles.getPropertyValue(customVar).trim();
            if (customValue) {
                return customValue;
            }
        }

        // Fallback to provided default
        return fallback;
    }

    private getConfig(): MermaidConfig {
        // Use Bootstrap CSS variables with fallbacks to ensure theme sync
        // Bootstrap 5 exposes CSS variables like --bs-primary, --bs-body-color, etc.
        return {
            startOnLoad: true,
            theme: 'base',
            themeVariables: {
                // Primary colors from Bootstrap theme
                primaryColor: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                primaryTextColor: this.getCSSVariable('white', null, '#ffffff'),
                primaryBorderColor: this.getCSSVariable('primary', '--scout-purple-dark', '#7413dc'),
                // Text colors from Bootstrap theme
                lineColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                textColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                // Background colors from Bootstrap theme
                tertiaryColor: this.getCSSVariable('light', '--light-grey', '#f1f1f1'),
                background: this.getCSSVariable('body-bg', '--white', '#ffffff'),
                mainBkgColor: this.getCSSVariable('body-bg', '--white', '#ffffff'),
                // Borders from Bootstrap primary
                border1: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                border2: this.getCSSVariable('primary', '--scout-purple-dark', '#7413dc'),
                // Note colors
                noteBkgColor: this.getCSSVariable('light', '--light-grey', '#f1f1f1'),
                noteTextColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                noteBorderColor: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                // Actor colors
                actorBorder: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                actorBkg: this.getCSSVariable('body-bg', '--white', '#ffffff'),
                actorTextColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                actorLineColor: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                // Signal colors
                signalColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                signalTextColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                // Label colors
                labelBoxBkgColor: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                labelBoxBorderColor: this.getCSSVariable('primary', '--scout-purple-dark', '#7413dc'),
                labelTextColor: this.getCSSVariable('white', null, '#ffffff'),
                // Loop colors
                loopTextColor: this.getCSSVariable('body-color', '--body-text', '#404040'),
                // Activation colors
                activationBorderColor: this.getCSSVariable('primary', '--scout-purple', '#490499'),
                activationBkgColor: this.getCSSVariable('light', '--light-grey', '#f1f1f1'),
                // Sequence colors
                sequenceNumberColor: this.getCSSVariable('white', null, '#ffffff'),
                // Section colors
                sectionBkgColor: this.getCSSVariable('light', '--light-grey', '#f1f1f1'),
                altBkgColor: this.getCSSVariable('light', '--light-grey', '#f1f1f1'),
                altBkgColorDark: this.getCSSVariable('gray-200', '--dark-grey', '#e0e0e0'),
            },
        };
    }

    initialise(): void {
        // Prevent concurrent initialisation attempts
        if (this.loading || this.initialised) {
            return;
        }

        this.loading = true;
        const config = this.getConfig();

        // Check if Mermaid is already loaded
        const windowWithMermaid = window as WindowWithMermaid;
        if (windowWithMermaid.mermaid) {
            try {
                windowWithMermaid.mermaid.initialize(config);
                this.mermaidAPI = windowWithMermaid.mermaid;
                this.initialised = true;
                this.loading = false;
                this.hideLoadingIndicators();
                this.setupMutationObserver();
                this.setupModalListeners();
                this.triggerRender();
                return;
            } catch (error) {
                this.loading = false;
                this.handleInitialisationError(error);
                return;
            }
        }

        // Dynamically import Mermaid (loaded on-demand, code-split into separate chunk)
        // Vite bundles Mermaid v10 as ESM with default export
        import('mermaid')
            .then((mermaidModule: unknown) => {
                try {
                    // Vite bundles ESM modules with default export
                    const mermaid = (mermaidModule as { default: MermaidAPI }).default;

                    if (!mermaid || typeof mermaid.initialize !== 'function') {
                        throw new Error('Invalid Mermaid module structure');
                    }

                    mermaid.initialize(config);
                    this.mermaidAPI = mermaid;
                    windowWithMermaid.mermaid = mermaid;
                    this.initialised = true;
                    this.loading = false;

                    // Set up MutationObserver to watch for rendered diagrams (persistent for SPA)
                    this.setupMutationObserver();

                    // Set up modal event listeners
                    this.setupModalListeners();

                    // Trigger rendering with explicit error handling
                    this.triggerRender();
                } catch (error) {
                    this.loading = false;
                    this.handleInitialisationError(error);
                }
            })
            .catch((error) => {
                this.loading = false;
                this.handleInitialisationError(error);
            });
    }

    /**
     * Trigger Mermaid rendering with explicit error handling
     */
    private triggerRender(): void {
        if (!this.mermaidAPI) {
            return;
        }

        // Try contentLoaded() first (Mermaid v10+ preferred method)
        if (typeof this.mermaidAPI.contentLoaded === 'function') {
            try {
                this.mermaidAPI.contentLoaded();
            } catch (error) {
                console.warn('Mermaid contentLoaded() failed:', error);
                this.handleRenderError(error);
            }
        }
        // Fallback to run() if available
        else if (typeof this.mermaidAPI.run === 'function') {
            this.mermaidAPI
                .run({ suppressErrors: false })
                .then(() => {
                    // Check for any diagrams that rendered
                    this.checkAndHideLoadingIndicators();
                })
                .catch((error) => {
                    console.warn('Mermaid run() failed:', error);
                    this.handleRenderError(error);
                });
        }

        // Also check for any immediate renders
        setTimeout(() => {
            this.checkAndHideLoadingIndicators();
        }, 100);
    }

    private checkAndHideLoadingIndicators(): void {
        document.querySelectorAll<HTMLElement>('.mermaid').forEach((element) => {
            // Check if SVG was rendered
            if (element.querySelector('svg')) {
                this.hideLoadingIndicator(element);
            }
        });
    }

    /**
     * Set up persistent MutationObserver for SPA compatibility
     * Only observes new containers, doesn't disconnect
     */
    private setupMutationObserver(): void {
        // Clean up existing observer if reinitialising
        if (this.mutationObserver) {
            this.mutationObserver.disconnect();
        }

        // Create persistent MutationObserver to watch for new diagram containers
        this.mutationObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const element = node as Element;

                        // Check if a new container was added
                        const container = element.classList?.contains('mermaid-diagram-block__container')
                            ? element
                            : element.querySelector('.mermaid-diagram-block__container');

                        if (container) {
                            // Start observing this new container
                            this.mutationObserver!.observe(container, {
                                childList: true,
                                subtree: true,
                            });

                            // Check if it already has a rendered SVG
                            const mermaidEl = container.querySelector<HTMLElement>('.mermaid');
                            if (mermaidEl) {
                                if (mermaidEl.querySelector('svg')) {
                                    this.hideLoadingIndicator(mermaidEl);
                                } else if (!this.processedDiagrams.has(mermaidEl)) {
                                    // New diagram, trigger render if API is ready
                                    this.processedDiagrams.add(mermaidEl);
                                    if (this.mermaidAPI) {
                                        this.triggerRender();
                                    }
                                }
                            }
                        }

                        // Check if this is an SVG or contains an SVG
                        const svg = element.tagName === 'SVG' ? element : element.querySelector('svg');
                        if (svg) {
                            // Find the parent mermaid container
                            const container = svg.closest('.mermaid-diagram-block__container');
                            if (container) {
                                const mermaidEl = container.querySelector<HTMLElement>('.mermaid');
                                if (mermaidEl && !this.processedDiagrams.has(mermaidEl)) {
                                    this.processedDiagrams.add(mermaidEl);
                                    this.hideLoadingIndicator(mermaidEl);
                                }
                            }
                        }

                        // Check for error indicators that Mermaid might add
                        const errorIndicator = element.classList?.contains('error')
                            ? element
                            : element.querySelector('.error');
                        if (errorIndicator) {
                            const container = errorIndicator.closest('.mermaid-diagram-block__container');
                            if (container) {
                                const mermaidEl = container.querySelector<HTMLElement>('.mermaid');
                                if (mermaidEl && !this.processedDiagrams.has(mermaidEl)) {
                                    this.processedDiagrams.add(mermaidEl);
                                    this.showError(mermaidEl, new Error('Mermaid diagram parsing failed'));
                                }
                            }
                        }
                    }
                });
            });
        });

        // Observe document body for new containers (SPA support)
        this.mutationObserver.observe(document.body, {
            childList: true,
            subtree: true,
        });

        // Observe all existing mermaid diagram containers
        document.querySelectorAll('.mermaid-diagram-block__container').forEach((container) => {
            this.mutationObserver!.observe(container, {
                childList: true,
                subtree: true,
            });
        });
    }

    private setupModalListeners(): void {
        // Prevent duplicate listener setup
        if (this.modalListenersSetup) {
            return;
        }
        this.modalListenersSetup = true;

        // Use event delegation on document to handle all modals
        document.addEventListener('shown.bs.modal', (event) => {
            const target = event.target as HTMLElement;
            if (!target.classList.contains('mermaid-modal')) {
                return;
            }

            const modalContainer = target.querySelector<HTMLElement>('.mermaid-modal__container');
            if (!modalContainer) return;

            // Extract block ID from modal ID
            const modalId = target.id;
            const blockId = modalId.replace('mermaid-modal-', '');
            const sourceDiagram = document.querySelector(`#mermaid-diagram-${blockId}`);

            if (!sourceDiagram) {
                this.showModalError(modalContainer, 'Source diagram not found');
                return;
            }

            // Retry logic: attempt to get SVG with retries
            this.copySvgToModal(sourceDiagram, modalContainer, 0);
        });
    }

    /**
     * Copy SVG to modal with proper ID reference correction and scaling
     */
    private copySvgToModal(
        sourceDiagram: Element,
        modalContainer: HTMLElement,
        attempt: number
    ): void {
        const sourceSvg = sourceDiagram.querySelector('svg') as SVGSVGElement | null;

        if (!sourceSvg) {
            // Retry if we haven't exceeded max attempts
            if (attempt < this.MAX_RETRY_ATTEMPTS) {
                setTimeout(() => {
                    this.copySvgToModal(sourceDiagram, modalContainer, attempt + 1);
                }, this.RETRY_DELAY_MS);
                return;
            }

            // Show error if retries exhausted
            this.showModalError(modalContainer, 'Diagram not yet rendered. Please wait and try again.');
            return;
        }

        try {
            // Clone the SVG deeply (including all styles, defs, and nested elements)
            const clonedSvg = sourceSvg.cloneNode(true) as SVGSVGElement;

            // Generate a new unique ID for the cloned SVG
            const originalId = sourceSvg.getAttribute('id') || '';
            const newId = `mermaid-modal-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
            clonedSvg.setAttribute('id', newId);

            // Global string replacement of originalId with newId in entire SVG innerHTML
            // This ensures all internal references (fill="url(#...)", markers, etc.) are updated
            const svgHTML = clonedSvg.outerHTML;
            const escapedOriginalId = originalId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const updatedHTML = svgHTML.replace(new RegExp(escapedOriginalId, 'g'), newId);

            // Create a temporary container to parse the updated HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = updatedHTML;
            const updatedSvg = tempDiv.querySelector('svg') as SVGSVGElement;

            if (!updatedSvg) {
                throw new Error('Failed to update SVG references');
            }

            // Get the viewBox from the original SVG
            const viewBox = sourceSvg.getAttribute('viewBox');
            if (viewBox) {
                updatedSvg.setAttribute('viewBox', viewBox);
                updatedSvg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

                // Calculate aspect ratio and scale to fit modal viewport (max 90% height/width)
                const modalBody = modalContainer.parentElement;
                const availableHeight = (modalBody?.clientHeight || window.innerHeight - 120) * 0.9;
                const availableWidth = (modalBody?.clientWidth || window.innerWidth - 80) * 0.9;

                const [, , vw, vh] = viewBox.split(' ').map(Number);
                const aspectRatio = vw / vh;

                // Calculate dimensions maintaining aspect ratio
                let width: number;
                let height: number;

                if (availableWidth / availableHeight > aspectRatio) {
                    // Height is the limiting factor
                    height = availableHeight;
                    width = height * aspectRatio;
                } else {
                    // Width is the limiting factor
                    width = availableWidth;
                    height = width / aspectRatio;
                }

                updatedSvg.setAttribute('width', `${width}`);
                updatedSvg.setAttribute('height', `${height}`);
            } else {
                // Fallback: use 100% height
                updatedSvg.setAttribute('height', '100%');
                updatedSvg.setAttribute('width', 'auto');
            }

            // Ensure styles are preserved
            updatedSvg.style.cssText = sourceSvg.style.cssText;
            updatedSvg.style.width = 'auto';
            updatedSvg.style.height = 'auto';
            updatedSvg.style.maxWidth = '100%';
            updatedSvg.style.maxHeight = '100%';

            // Clear and add the updated SVG
            modalContainer.innerHTML = '';
            modalContainer.appendChild(updatedSvg);
        } catch (error) {
            this.showModalError(modalContainer, `Failed to display diagram: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private showError(element: HTMLElement, error: unknown): void {
        const errorMessage = error instanceof Error ? error.message : 'Failed to render diagram';
        element.classList.add('mermaid-diagram-block__error');

        // Hide loading indicator
        this.hideLoadingIndicator(element);

        // Create or update error message
        let errorContainer = element.parentElement?.querySelector<HTMLElement>('.mermaid-diagram-block__error-message');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'mermaid-diagram-block__error-message alert alert-danger mt-2';
            errorContainer.setAttribute('role', 'alert');
            errorContainer.setAttribute('aria-live', 'polite');
            element.parentElement?.appendChild(errorContainer);
        }

        errorContainer.textContent = `Error rendering diagram: ${errorMessage}`;
        errorContainer.style.display = 'block';
    }

    private showModalError(container: HTMLElement, message: string): void {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert" aria-live="polite">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    private hideLoadingIndicator(element: HTMLElement): void {
        const container = element.closest('.mermaid-diagram-block__container');
        if (container) {
            const loadingEl = container.querySelector<HTMLElement>('.mermaid-diagram-block__loading');
            if (loadingEl) {
                loadingEl.style.display = 'none';
            }
        }
    }

    private hideLoadingIndicators(): void {
        document.querySelectorAll<HTMLElement>('.mermaid-diagram-block__loading').forEach((loading) => {
            loading.style.display = 'none';
        });
    }

    private handleInitialisationError(error: unknown): void {
        console.error('Failed to initialise Mermaid:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';

        // Show error on all diagram containers
        document.querySelectorAll('.mermaid-diagram-block__container').forEach((container) => {
            const mermaidEl = container.querySelector<HTMLElement>('.mermaid');
            if (mermaidEl) {
                this.showError(mermaidEl, new Error(`Initialisation failed: ${errorMessage}`));
            }
        });
    }

    private handleRenderError(error: unknown): void {
        console.error('Error rendering Mermaid diagrams:', error);
        // Find diagrams that failed to render and show errors
        document.querySelectorAll<HTMLElement>('.mermaid').forEach((element) => {
            if (!element.querySelector('svg') && !this.processedDiagrams.has(element)) {
                this.showError(element, error);
            }
        });
    }
}

export default MermaidInitialiser;
