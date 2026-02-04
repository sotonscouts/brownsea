import 'bootstrap/js/dist/collapse';
import 'bootstrap/js/dist/dropdown';
import 'bootstrap/js/dist/modal';
import 'bootstrap/js/dist/scrollspy';

import PhotoSwipeLightbox from 'photoswipe/lightbox';
import 'photoswipe/style.css';

import './scss/main.scss';
import MermaidInitialiser from './mermaid';

// Initialise PhotoSwipe
document.addEventListener('DOMContentLoaded', () => {
    const lightbox = new PhotoSwipeLightbox({
        gallery: '.gallery',
        children: 'a',
        pswpModule: () => import('photoswipe')
    });

    lightbox.init();

    // Initialise Mermaid diagrams only if diagrams are present on the page
    if (document.querySelector('.mermaid')) {
        MermaidInitialiser.getInstance().initialise();
    }
});

