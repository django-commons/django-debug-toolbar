Design Guidelines
=================

These guidelines describe the Django Debug Toolbar brand: its logo, colors and
typography. They exist to keep the project's visual identity consistent across
the toolbar UI, the documentation, the website and any community materials.

The brand assets referenced below live in ``docs/_static/brand/``. The full set
(every color variant of every layout) is available there as both ``.svg`` and
``.png``, the SVGs are used throughout this page, while the PNGs are provided
for contexts that cannot use SVG.

Logo
----

The logo combines a **logo element** (the stylized "D" fan) with the **Django
Debug Toolbar** wordmark. In the colored variants, only the word "Debug" is set
in Signal Green; "Django" and "Toolbar" stay in the neutral color.

Do not alter the logo (such as changing its color, shape, orientation, or
layout) or add effects without approval from the project maintainers.
Everything you need has been made available, so always use the supplied files.

Primary wordmark
^^^^^^^^^^^^^^^^^

The inline wordmark is the primary lockup. Use it wherever horizontal space
allows.

.. raw:: html

   <p><img src="_static/brand/Wordmark-Inline-Coloured-Dark.svg"
           alt="Django Debug Toolbar inline wordmark"
           style="max-width: 480px; width: 100%; height: auto;"></p>

Layout variants
^^^^^^^^^^^^^^^

Use the stacked or columns lockups when the available space is more square than
wide, for example in a sidebar or a social avatar.

.. raw:: html

   <p style="display: flex; flex-wrap: wrap; gap: 32px; align-items: center;">
     <img src="_static/brand/Wordmark-Stacked-Coloured-Dark.svg"
          alt="Django Debug Toolbar stacked wordmark"
          style="width: 190px; height: auto;">
     <img src="_static/brand/Wordmark-Columns-Coloured-Dark.svg"
          alt="Django Debug Toolbar columns wordmark"
          style="width: 210px; height: auto;">
   </p>

Logo element
^^^^^^^^^^^^

The logo element can be used on its own as a compact mark, a favicon or an
ornament.

.. raw:: html

   <p><img src="_static/brand/Logo-Element-Black.svg"
           alt="Django Debug Toolbar logo element"
           style="height: 96px; width: auto;"></p>

App icons
^^^^^^^^^

Square icons are provided on each of the brand's background colors for use as
app icons and favicons.

.. raw:: html

   <p style="display: flex; flex-wrap: wrap; gap: 16px; align-items: center;">
     <img src="_static/brand/Square-Green.svg" alt="Green app icon"
          style="width: 96px; height: 96px; border-radius: 12px;">
     <img src="_static/brand/Square-Dark-Blue.svg" alt="Dark blue app icon"
          style="width: 96px; height: 96px; border-radius: 12px;">
     <img src="_static/brand/Square-Light-Blue.svg" alt="Light blue app icon"
          style="width: 96px; height: 96px; border-radius: 12px;">
     <img src="_static/brand/Square-Black.svg" alt="Black app icon"
          style="width: 96px; height: 96px; border-radius: 12px;">
   </p>

Choosing a variant
^^^^^^^^^^^^^^^^^^^

Each lockup ships in four color variants. Pick the one that keeps the logo
legible against its background:

- **Black** – neutral logo on light backgrounds.
- **White** – neutral logo on dark backgrounds.
- **Colored (dark)** – green "Debug" with black text, for light backgrounds.
- **Colored (light)** – green "Debug" with white text, for dark backgrounds.

Colors
------

The primary colors are Signal Green, Trace Cyan, System Teal and Runtime Black.
Each has five shades, from the fully saturated ``1`` down to the lightest
``5``. All other colors are supporting accents or lower-opacity tints of these.

In the toolbar UI these map directly to the theme: Signal Green is the
structural and data color (table borders, timeline bars), Trace Cyan is the
panel surface, System Teal is the dark-mode surface, and Runtime Black is the
sidebar and text.

.. raw:: html

   <style>
     .djdt-swatches { border-collapse: collapse; margin: 12px 0; }
     .djdt-swatches td { padding: 4px 10px; border: none; font-family: monospace; }
     .djdt-chip { width: 28px; height: 28px; border-radius: 4px;
                  border: 1px solid rgba(0,0,0,0.1); display: inline-block;
                  vertical-align: middle; }
   </style>
   <table class="djdt-swatches">
     <tr><td colspan="6"><strong>Signal Green</strong></td></tr>
     <tr>
       <td><span class="djdt-chip" style="background:#30C16E"></span></td><td>#30C16E</td>
       <td><span class="djdt-chip" style="background:#6ED499"></span></td><td>#6ED499</td>
       <td><span class="djdt-chip" style="background:#ACE6C5"></span></td><td>#ACE6C5</td>
     </tr>
     <tr><td colspan="6"><strong>Trace Cyan</strong></td></tr>
     <tr>
       <td><span class="djdt-chip" style="background:#38BBE8"></span></td><td>#38BBE8</td>
       <td><span class="djdt-chip" style="background:#73D6F8"></span></td><td>#73D6F8</td>
       <td><span class="djdt-chip" style="background:#E0F8FF"></span></td><td>#E0F8FF</td>
     </tr>
     <tr><td colspan="6"><strong>System Teal</strong></td></tr>
     <tr>
       <td><span class="djdt-chip" style="background:#014A5F"></span></td><td>#014A5F</td>
       <td><span class="djdt-chip" style="background:#4D8EA0"></span></td><td>#4D8EA0</td>
       <td><span class="djdt-chip" style="background:#CCDFE4"></span></td><td>#CCDFE4</td>
     </tr>
     <tr><td colspan="6"><strong>Runtime Black</strong></td></tr>
     <tr>
       <td><span class="djdt-chip" style="background:#131313"></span></td><td>#131313</td>
       <td><span class="djdt-chip" style="background:#999999"></span></td><td>#999999</td>
       <td><span class="djdt-chip" style="background:#E6E6E6"></span></td><td>#E6E6E6</td>
     </tr>
   </table>

The complete palette, including every shade:

.. list-table::
   :header-rows: 1
   :widths: 20 16 16 16 16 16

   * - Family
     - Shade 1
     - Shade 2
     - Shade 3
     - Shade 4
     - Shade 5
   * - Signal Green
     - ``#30C16E``
     - ``#6ED499``
     - ``#ACE6C5``
     - ``#D6F3E2``
     - ``#EAF9F0``
   * - Trace Cyan
     - ``#38BBE8``
     - ``#73D6F8``
     - ``#B3ECFE``
     - ``#C9F2FF``
     - ``#E0F8FF``
   * - System Teal
     - ``#014A5F``
     - ``#4D8EA0``
     - ``#9ABEC9``
     - ``#CCDFE4``
     - ``#E6EFF1``
   * - Runtime Black
     - ``#131313``
     - ``#4D4D4D``
     - ``#999999``
     - ``#CCCCCC``
     - ``#E6E6E6``

Typography
----------

Two typefaces carry the brand, both free and usable for web and print:

- **Alef** (Bold) – used for headlines and panel titles.
- **Geist** and **Geist Mono** – used for body text, with Geist Mono reserved
  for code, calls to action and other monospace contexts.

In the toolbar UI, panel titles are set in Alef Bold, general text in Geist,
and code samples in a monospace stack. Both fonts are self-hosted so the
toolbar keeps working offline and under a strict Content Security Policy.

Credits
-------

The Django Debug Toolbar brand and logo were designed by Robin of
`RBNX Studio <https://www.rbnx.studio>`_. Thank you for giving the project its
visual identity.
