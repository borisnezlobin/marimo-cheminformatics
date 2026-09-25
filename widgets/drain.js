const FONT_URL = 'https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;600;750&display=swap';
const CSS = `  .drain {
    --page: #E4EAE8;
    --surface: #F6F8F7;
    --ink: #1A2124;
    --muted: #56636A;
    --quiet: #D5DDDA;
    --strong: #1A2124;
    --strong-ink: #F6F8F7;
    --cooling: #5B686E;
    --good: #3E9B6A;
    --focus: #4F8DB8;
    --star: #D9A92E;
    --star-off: #9AA7A2;
    --board-paper: #EDF1F0;
    --shadow: 0 1px 2px rgba(26, 33, 36, 0.08), 0 12px 32px rgba(26, 33, 36, 0.14);

    --text-sm: 0.875rem;
    --text-md: 1rem;
    --text-lg: 1.125rem;
    --text-xl: 1.5rem;

    --radius-control: 12px;
    --pad-card: 12px;
    --radius-card: calc(var(--radius-control) + var(--pad-card));
    --inset-board: 10px;
    --radius-board: calc(var(--radius-card) + var(--inset-board));
    --gap: 12px;
    --ease: cubic-bezier(0.2, 0, 0, 1);

    font-family: "Atkinson Hyperlegible Next", "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
  }

  .drain {
    background: var(--page);
    color: var(--ink);
    padding-inline: 16px;
    padding-block: 20px 36px;
    font-size: var(--text-md);
    line-height: 1.5;
  }
  .stage {
    max-width: 460px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: var(--gap);
  }
  .top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--gap);
  }
  .level-heading {
    margin: 0;
    font-size: var(--text-xl);
    font-weight: 750;
    line-height: 1.2;
    text-wrap: balance;
  }
  [hidden] { display: none !important; }

  .icon { display: inline-flex; width: 1.2em; height: 1.2em; flex: none; }
  .icon svg { width: 100%; height: 100%; }

  .button {
    appearance: none;
    border: 0;
    font: inherit;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: var(--radius-control);
    background: var(--quiet);
    color: var(--ink);
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    transition-property: transform;
    transition-duration: 150ms;
    transition-timing-function: var(--ease);
  }
  .button:active { transform: scale(0.96); }
  .button:focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; }
  .button:disabled { opacity: 0.4; cursor: default; }
  .button--primary,
  .button[aria-pressed="true"] { background: var(--strong); color: var(--strong-ink); }
  .hit {
    appearance: none;
    position: absolute;
    border: 0;
    padding: 0;
    background: transparent;
    border-radius: var(--radius-control);
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    transition-property: background-color;
    transition-duration: 150ms;
    transition-timing-function: var(--ease);
  }
  .hit:hover:not(:disabled) { background-color: rgba(26, 33, 36, 0.05); }
  .hit:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
  .hit:disabled { cursor: default; }
  .hit--nudge { animation: nudge 1.2s var(--ease) infinite; }
  @keyframes nudge {
    from { box-shadow: 0 0 0 0 var(--focus); }
    to { box-shadow: 0 0 0 14px transparent; }
  }
  .button--stack { flex-direction: column; gap: 2px; }

  .board {
    position: relative;
    border-radius: var(--radius-board);
    overflow: hidden;
    box-shadow: var(--shadow);
    background: var(--board-paper);
  }
  canvas {
    display: block;
    width: 100%;
    max-width: 100%;
    aspect-ratio: 400 / 560;
    touch-action: manipulation;
  }
  .score {
    position: absolute;
    top: var(--inset-board);
    right: var(--inset-board);
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(246, 248, 247, 0.9);
    color: #1A2124;
    font-size: var(--text-sm);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
  .tip {
    position: absolute;
    left: 50%;
    max-width: calc(100% - 2 * var(--inset-board));
    padding: 8px 14px;
    border-radius: 999px;
    background: var(--strong);
    color: var(--strong-ink);
    font-weight: 600;
    text-align: center;
    text-wrap: balance;
    box-shadow: var(--shadow);
    pointer-events: none;
    opacity: 0;
    transform: translate(-50%, calc(-100% + 4px));
    transition-property: opacity, transform;
    transition-duration: 200ms;
    transition-timing-function: var(--ease);
  }
  .tip[data-visible="true"] { opacity: 1; transform: translate(-50%, calc(-100% - 8px)); }
  .tip::after {
    content: "";
    position: absolute;
    top: 100%;
    left: var(--caret, 50%);
    width: 16px;
    height: 9px;
    background: var(--strong);
    clip-path: polygon(0 0, 100% 0, 50% 100%);
    transform: translateX(-50%);
  }
  .tip--below::after { top: auto; bottom: 100%; clip-path: polygon(50% 0, 100% 100%, 0 100%); }
  .tip--below { transform: translate(-50%, 4px); }
  .tip--below[data-visible="true"] { transform: translate(-50%, 8px); }

  .result {
    position: absolute;
    inset: var(--inset-board) var(--inset-board) auto var(--inset-board);
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: var(--pad-card);
    border-radius: var(--radius-card);
    background: var(--surface);
    color: var(--ink);
    box-shadow: var(--shadow);
  }
  .result-head, .meter, .reveal { padding-inline: 6px; }
  .result-head { display: flex; justify-content: space-between; align-items: center; gap: var(--gap); padding-top: 4px; }
  .result h2 { margin: 0; font-size: var(--text-xl); font-weight: 750; line-height: 1.2; }
  .meter { display: flex; align-items: center; gap: 10px; }
  .meter-track { flex: 1; height: 8px; border-radius: 999px; background: var(--quiet); overflow: hidden; }
  .meter-fill { display: block; height: 100%; background: var(--good); }
  .meter-value { font-weight: 600; font-variant-numeric: tabular-nums; }
  .reveal { margin: 0; color: var(--muted); text-wrap: pretty; }
  .reveal strong { color: var(--ink); font-weight: 750; }
  .actions { display: flex; gap: 8px; }
  .actions .button { flex: 1; }
  .stars { display: flex; gap: 3px; }
  .star { display: inline-flex; width: 24px; height: 24px; color: var(--star-off); }
  .star.on { color: var(--star); }
  .star svg { width: 100%; height: 100%; }

  .level-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--gap); }
  .world {
    display: flex;
    gap: 14px;
    align-items: flex-start;
    padding: var(--pad-card);
    border-radius: var(--radius-card);
    background: var(--surface);
    box-shadow: var(--shadow);
  }
  .world-art { width: 56px; height: 56px; flex: none; object-fit: contain; }
  .world-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .world-name { margin: 0; font-size: var(--text-lg); font-weight: 750; }
  .world-enzyme { margin: 0; color: var(--muted); font-size: var(--text-sm); }
  .world-levels { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 8px; }
  .level-button { align-items: flex-start; text-align: left; }
  .level-button.current { box-shadow: 0 0 0 2.5px var(--ink); }
  .level-stars { display: flex; gap: 2px; }
  .level-stars .star { width: 16px; height: 16px; }

  .about { color: var(--muted); font-size: var(--text-sm); }
  .about summary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-weight: 600;
    list-style: none;
  }
  .about summary::-webkit-details-marker { display: none; }
  .about summary:focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; border-radius: 4px; }
  .about p { margin: 8px 0 0; text-wrap: pretty; }
  .visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  @media (prefers-reduced-motion: reduce) {
    .button, .tip { transition-duration: 0ms; }
    .hit { transition-duration: 0ms; }
    .hit--nudge { animation: none; box-shadow: 0 0 0 3px var(--focus); }
  }

  .drain {
    border-radius: var(--radius-board);
    padding-block: 20px;
  }
  .drain:focus { outline: none; }
`;
const MARKUP = `<main class="stage">
  <div class="top">
    <h2 id="level-title" class="level-heading">Find the rhythm</h2>
    <button type="button" class="button" id="show-levels" aria-pressed="false">
      <span class="icon" data-icon="squares-four"></span>All levels
    </button>
  </div>

  <section id="game-view" class="stage">
    <div class="board">
      <canvas id="board" role="img" aria-label="A beaker of medicine draining into a row of liver enzymes"></canvas>
      <div id="hits"></div>
      <span class="score" id="score">0% in the green</span>
      <p class="tip" id="tip" aria-hidden="true"></p>
      <section class="result" id="result" hidden aria-live="polite">
        <div class="result-head">
          <h2 id="result-title"></h2>
          <div class="stars" id="result-stars" role="img"></div>
        </div>
        <div class="meter" id="result-meter" role="img">
          <span class="meter-track"><span class="meter-fill" id="result-fill"></span></span>
          <span class="meter-value" id="result-value"></span>
        </div>
        <p class="reveal" id="result-reveal"></p>
        <div class="actions">
          <button type="button" class="button" id="retry"><span class="icon" data-icon="arrow-counter-clockwise"></span>Try again</button>
          <button type="button" class="button button--primary" id="next"><span class="label">Next level</span><span class="icon" data-icon="arrow-right"></span></button>
        </div>
      </section>
    </div>
  </section>

  <section id="levels-view" hidden>
    <ol class="level-list" id="level-list"></ol>
  </section>
  <p class="visually-hidden" id="announcer" aria-live="polite"></p>
</main>`;
const SPRITES = {"cyp2d6": "data:image/png;base64,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", "cyp2d6_dead": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJYAAACVCAYAAAC6lQNMAACWA0lEQVR42uy9d3hVdbY+/u69T2/JSe+kAWkQSqgJJKF36YICggIqRZoKSglRBCyACoJ0QQWl916S0EKvCSEhCSE9pJycXnb5/bHP2RPUma9zZ+6dufc324eHh5icnLM/a6/yrne9i1i7dm0Xo9GY99FHHzXgP9d/rn/wWrFihValUkWRRqMxz8PDw/ifW/Kf659xeXh4GI1GY95/7sR/rv9c/7n+91zEf27ByxfHcURGRgaVn59PaLVadvTo0cx/7sp/Hob/yms1fT3yPw/f/8+uPXv2UE3/nZaWJvqvHrzztYimr+V6PY7jNCdPnpyVkZEx78qVK13FYvEfGeD/1ANE/NHXOI4jABBpaWmijRs3ipvci/9crgO9ePGi6LdG8wffRwKAWq0Gx3ESrVb7h6/1J38nCQByuRwcx0k4jqOaGNzAlJSUmuDgYC4qOooLDg5mR48e/TPHcTLnzxH/A/eEBND0flDt27cX/ye1+ZN5zJ+9MS6jO3z48PDx48dfmTBhQsXQoUPvzp8/fxzHcWKO4yTufzE0ymU4f8vrXbp0qffkyZNPTJgwoXLY0KEFH3zwwZzdu3d/HB4ezjRv0YL7as1q20+7d9knvfWmw8vLixszZsyHAPB3HPA/YlSueyTmOE5MEPwtcXd3d31N5HwgxBkZGaOys7NnnzlzZpRcLv/da/z/zUuRAKBQKHD58uVXr1+//t65c+eGyWSyv+qFNm3aNCUmJoYLDgnh+g3oz8W1iuM0Gg0XFxdXMXbs2Mphw4bdX7Ro0bg/OiDXlZycLAKAs2fP9mvbti3n6+vL9ejZk4uNi+P8/Pw4b29vLio6ijt68gSbcSmLO3nmNHfr7h2mS2JXumPHjlUcx2mahKH/tvvCcVz4/I8++u6dd94pnzRpUmWv3r1X9O7d+72xY8bcHT16dOWbkyZVpKenV/Xq1avS39+fi4mJ4QICArg+vfvcXLVqVeD/L43L5TEKCwtDxo0bdzskJISLjY3lAgMDuX79+l3ds2dPYHJysigtLU0CQOQ8SE2f3r1Lw8LD6VNnzziu3bjOZlzKYuYv/IiObxPP9ezVi4uJjeWaNWvGjRgxYj3HcZF/EBqJUaNGURzHqYcNG3bX09OT++GnnfaLl7LYPfv3MQDssXFx9jPnz7Enz5zmjhw/xh0+dpS7fO0q++qYMVzr+PhGjuNEycnJIqfXIP/ZRuV8fwHDhg0rlojFnFgs5pRKJQeAk0qlXFh4ONe3fz8uIjKSA8CJRCJu+swZzM5dP9mXfpLu8PLy4tq0a5NbVFTUDAD53/UA/NtdGzduFANAeXl5SFJSUoGHhwc3a+4cx7Yd2+0LFn5k9/Ly4vr06XNciGkUBY7jyPPnz38QFBjITZsx3XH52lXu4JHD3LGTJ7gzF85x5zMvsnce3mdHj3mVAWAXiURc9+7dn+/evTuiaZXX1Bv06tWL6z9wAHv89Elu/6GD3IhRIzmVSsX9un8vd/3WTe7wsaPc0RPHuSPHj3EXL2WyPXr1ZACYJ02dlPSbj0RevHhR9Ceqyv9n8j9q1CgKAJYuXbpKIpFwySnJ1l/2/spu2/ED27ZdO8fUd962n71wnrl6PZvNvHKZnfjmJHbU6FHszXu3uWOnTnDXbl7nPvxogY0kSW7O3LkXnYZP/SvPW/Q/kU8RBEG8/fbbDrPZHDxw4MDzBQUFkctWfEZHRUWLjEYjWrRsyRn0RvrnH3/svXDhwpVeXl4l2dnZoaNGjXotMyszqLFRz7WOjxeZTCaIxCLhiMQiMfHhvPdxI/s68fHihaSnp5fj+/Xrg+fPn39x7dq1vWbOnFnwm7DAgAPXUF9PyOQyVFdV4+jhI5gw8Q34+PjgRe0LqDVqEAQJq9WC+vp6IiUlBfV19fJTR0+dmjFjxserV6+mxWLxbYlEcj01NZVtalAkSbIMw/zOgKRSKWe327Fnzx7qt7hYWlqaJD093c5xXEBCQsKkiMhI5qs1qyUSiYSgaRrLln8mkkgkcDgcqKmpgUwmwytDh2L/vn24f/c+QpqFAAAC/P0lHMc5zpw+nXQsNTUBwI0/+n3/JwwrLS2NJAiClcvl3O7du0f27t17+bVr1yI3btlEd+7cRZSTmwOCIKDX64nAoECRTqfDd999N18ul6OysvIvb1IkIsQSMSRSCWx2G1iWxbWrV/Hrrl+gNxiw9YdtiG3VCgxNi5OSkui3Jk0K3rlz5z6pVNo6PT2dA4DOnTvL9wJlfv5+2w8ePPjmlyu+oA1Gg4iiKPTp2xdmsxnPS56jrq4Obm5uiIiIQHBwMNrEtyGGjxiBYa8MVe7evfuba9eyQdMOuk+fPvs/+uij84mJibvkcrmJJEnMmzdvXbNmzYY8f/6ccXoMViKRkIMGDbq7f//+kQRBOJyei0tOThZlZmZy6enpdg8PDyxbtmz+04Kn2m/Xr6UlUilh0OshEomgVquh0+lAURTEYjEcDgdkMhnatGmDY0eOQiKRQCwR48rlK+A4jnj27Jno0qVL/QHcGD169P895D0tLY1MT09nCwsLQxYvXrz/wvnzCVXV1QDA+vv7kzPem4nUHj1QXVMNh8OBg/sPQKlSISGhPX382HGu9kUtMXL0KFIsEpE/7fwRIrEYI0ePQmhYKIwGA7Zt2YbwiHC8MWki3NzcYDQYIBKJodVq8c3X39gPHThA3bp1a3SrVq0O1NbWkgRBsBzHiVq2aHk2vyA/RSqVMjabjQKAxKREJHTsCD9fX7Ach8yMDNzIvo6k7t3g6eGJ0PAwHD54iLt39y7j4+PD1dTUiAmCQMuWLeHp6Vkhl8vP1NTUmCoqKqZ3T0lGr969oNPpwHEcal/U4eedO+Hj43Nq67ZtKzp27HgZAEcQBEcQBHbu3Dn68uXL848ePdqOZmj20NEjJEEQ4DgOBEGApmnoG/VgGAYkSYKiKMhkMri5u8FkMqH0eSkKCgqQ/+QJMi5epMvLykWdO3d+NTs7e4/TuJn/M4aVlpZG5ubmEl9++WXIuHHjzhQUFEROfHMSHRQcRD4veU4ePXIEeY/zsDhtCYaPGIFTp07h4YOHmDJ1Chp0DSh9XorEpCRIpRIAgMViwaYNGyFXyDFwyGDodY3QarUIDAqE2WyGw+GAiBKh8Gkhnpc+xy8/7+Lu3LlDJCYm1g8fPtxgs9n0R44c+aa6unq42WweMP6NCWzXxK7ki9pa7Nn9Ky6ev4Av16xCu3btwLIsGht1SF+yFPX19ZDKZHhaUNDEe1IgCJJzOBwsAK6p1589by47feZ0wmQycyRBgGM5yGQy4tatW8w7U6aKNBoNwsLCnkVGRpI1NTVfaTSakHv37r1vtVqhdtOwD+8/IBenLcEbkyaioaEBFMWnSTabDTarDRzHQSaXgaIo3tAoCjKpFAzLwmwy41lxMf3e9JmikJDg9x88eLCKZdn/O4bl9FQkSZL0+PHjbx49dizhh507HC2jWootFjMkEilMZhPSF6fh7Jmz+GXvHhiNRpSXlyO+TTyKC4sRGhYKL29vOGx2gAREIhEkYgkaGxthc9ggpsRQazQwmYxgWRZSiRQPHz6EyWREeFg4DAYD9u3bh7u376C0tBQAIJFIwHEcln++gu3StSup1xsgl/MQx4Vz5xEYHIToqGjY7XY4HA6AADw8PCAWi1H2vBRPCwuR/+QJdv28Cwa9Hmq1Gq3j41FeXs4+Ky7mkrolcd9+953IarEIvw8A73UYGn169GIYlqU6duwAs8WCirJyvHjxAnGtWzEfL1pIkCRFbv5+I44dPYr3P/wAyakpsFosoBkGWRmZCAlphn4D+sNqtcCFbbm8ms1mQ31tHXx8fZkP3/+A8vfze3To8KFWtIMmAbD/F3IsMj09nSUIgv36668XzZ41q23XpCQ6IjJCXFNTA4qiYDQYIVcqMOf9ebhw/gKuXb2KbsndoTfo4XA4EBQcBLVaDYamQRAAQZBgGRYWxoKrV66gvqEBYaFhiGsdB72+ERQpQl1dHUwmE2JiYkCAhK+/Hz79bBlMRhP36NEj7s6tW7DabEx9XT1p0BuomzduwM3dHeAAD08PdEnsCofNDplMBpPZBJVKBaVKCZqm4XA4ENwsBKHhYRg4eBC6Jydjw7rv0KlLFyR0TMCTx3nkpUuXMXLUSAAcSIoEQzMoLi5GQX4+pDIpDu4/AIahqe83b+YiIiI4kiRx5fJlZt6cuUTHDh1FIpEINE1j3gfvQyyR4KsvvsSWTZthsVjQrXt3VFZWwMPDEwMHDxSMyWW0wo0nSdA0DavVCo7jjOD+tSjAP9OwSAAsx3HNPvjgg+lffPHFB+07dODGvv4aUVRYBLVa/dJTXPeiFgRBgCBIaD08UFLyHBvWrcekNydBGxEOh4OGWCSCxekBGhsbQYkoeHp6IjIyEgQIcBxAkAQkEgmCgoNAkhRkchlIioSzgiQ6de5ExMbGoqysjKyoqIC7uzv8/Pz4QsBmw43sG6irq8XgIYNhMBpgs9kgl8tB0zRYlhVCEcdxMBqNiImNwaqv1yDvcR7AAW3btUNSt25QKBSgaRpGoxGlz0thtVoBAFWVVTAYDJg2cwaCQ0KIqqoqgiRJtGnblgwKCkJdXR0IgsDZ02dRXFwMfWMjAECn00GhUCA6NgapvXog92EOHA7HS8bEcRzEYjEfMjng0cOH3NOCAoDjvmUY5l/a4hH9kyAFUiKRsCtXrlzUuXPnubm5udqhw4cxb02eTDkcDtjtdhgMBojEIkilUjTUN2DJosUwmUzYvetnGAwGPHr0EFkZmcjLy4OHhwdYlkWvXr3Qt38/sBwLs9mMhIQOcNe641nRMxiMekilMjQ0NECj0QAATCYTfHx9YbVaQJIkGIaByWSCXCGH1WpFeEQENGo1FEoFCBDQarXo2bsnxo15DdVVVZg+ayZIkoTVaoWrRcJxHEiSFA7UZei+fr4AAJbl35tEyofastIy+Pj4QCwWg2zeHBRFoWtiIkiShMloFEKyw2EHANy5cwcPHj5A7qMcNG/RHFKJFNExMbDb7Yhv0wYDBw2EwWCArl4HmqZfCoMiEe+tb928CZPJjO/Xr4dIJEKvXr0qb9++TYwaNYrau3fv/064Yc+ePRRBEMyePXuGLFy48FOCJDB95gy6Z69eIpPRBJZjhYOhHTSUSiWqK6ug9fBAz969YHbeEJZl4eHhgeKiImjUGqjUKnz5xRfYv38/Xh07Bl26doHNbsOD+w/g4eGBgKBAgOOg1qhx7+495Obk4Nq1a5g0aRL/umYzSJKEw+6AXq+HQiEHx7JwshXAsiwsFgs8PDzw3uzZ+HjBAgwYPAj+/v6w2WwwGo1CjmU0GoUDdX0WkdObEgQBsVgMpUKJoqIi0DQNESWCzWYDQRBgWRYajQYcx8FsNgMANBoNLl68KOR/3t7e+Gn3LsTExgAAjEYjGuobwLKskEMFhwSDIinYHXaQJCmAyHmP83D3zl2wDAO5TEaUl1fAaDR+IJfLM/bu3Wt3RZL/acP6h9HZvXv3QqVSQaVS/Xzv3j2/Ldu3MVHR0SKTyQSCJF5y3VKZFBRFweFwoGevXujVuzf69O2DHj16oKDgKViWxUcff4SPFy/EiFEjERsXh10//QS93oARo0bheclz2G02xLaKg93G41lKpRIikQjXrlxBxsUMPHr4CAMHDQLLstA36mG1WmGz2iCTyaFWqyGVScFxHEBAOLTI5pG4euUqHufmokevnrDb7SBAoKTkGR7nPEZoWCgYhnnps7AsC5vNCpav/KBUKlFfVwe9Xg8fPx/Y7XYh7MtkMihVSnAsB7FEjOLiYmzfuhVSqRQBAQFY883XiGvdCiaTCQzD8NiUWAzaQQMEAZvVise5jxHfJh4cx4FhGHAcB62HFjeyryP/ST6mvD0V49+YQCqUSm7L5i1hrVq1Spk/f37VqVOnnjrPmftfZVgAIJPJ0KxZs49phtEOGDgADfUNBCWihDACADTtgLu7O3Q6HXQNDZDJZDAajWAYBiGhzdCrT2/0H9Af7RMSYDAYYDAY0KpVK2i1WuzbsxcRkRG4fOkSAAJBwcEwGox8GW6zISAgACRFgeNYdOnaFc1Cmwl5kcu7mEwmPM7NRUBgoPCeSIoEx3GwWW0IDApEQ309YuJiIRaLUV5ehl9/+QW3bt5CSLMQNGvWTPBCUqkU7m7ukMnlIAhApVKBpmmoVCrcvHEDIpEIPr6+EItE4Jxe1fVzKpUK1ZVVuJSZBZVKhdQePdCvf380NjZCJBIJYY5hGBgMBpAkCbVajXNnzuHu3btITk2BQqGAWCzG5UuXkXHxIqbPmIGw8DAQBIEuXbsQsXGx1J3bd8LOnz8/vltS0ov8/PwbycnJopKSEvZ/lWE50fHpxUVFHn369eU8PD0J0plU2+12Z17CISgoCNu3bsflrEtITkkBJaKg9dCCYRjhplssfH5EkiTsdjv8/P1wxXkDb964gdQeqQgNDXVVP2BZFrW1tWBZFj1790anLp2gUCiE/+8ybovFApPRiNCwMOE92yx8yDObzfDx8YFcLodcoYBarcaD+w+g1mjw+vhxOLj/AFQqJYKCg8HQDPLz8nH9ejbKSktRXVUNqVQGrVbLezSCwC+7diP76jXY7Da0bt0aIpFI8DIkScLhoCGVyxAcFIyWUVFQKBQgCRIO2gGKokBRFOx2OyQSCdw0bpDJZIhr1QrbtmzF8aPHQTscOHH8BL79+muER0Ri1OhRaHQm/VarFeHh4RgxaiRjdziY48eODX517Ks1hw4euvE/6bn+KYblzFdmNTQ0eDwrfsa5u7sRFqsVUpkUYrEYEqkUBEmCZRk8fPAAe/fsQWK3RDRv0QJ2O58zsCwLlmUFbwLwZLynBU8RExsDqVQGhmMxcdKkl363RCJBZUUFn7h7e4NheSOVSqWQSCXOypPPgwIDA2Ey8uHGYrbAYrEIXo1lWegaddBoNJBKpaiqrARD0+jSpSsiIyNRkF+AQwcPYuP33+P+vfuQSqW4d+8edv30M/bv3QeL1QqCJISwuWXTZmRlZqK2thZdunYFRVEgCAIGvQEcxyE2NhYxsbHQarWwWW0CCGq322G32yGVSiGTyUASJAgASpUKXZMSYTaZkfckD23btsXwEcORffUauiV3h0gkAsuyglFarVYyNTUVpaWluH4tu1Ntbe3P6enpBo7jiPT09P8dVaGTiYBmoaFISkpEXl4eKsor0LN3L8S1ioPDbndWQg7IFXIwDIOb12+gS9eufL7TBJNxGRlFUSguKobRaMSgwYNx984dxDoPwoVKcxwHq9WK0PBwiEQUbFYbKIrik16SgISSQCqVgmVZNNQ3wGw2C22SpiW7y5Oo1RpQFAWRSAS73Y5AZ9j08vbGgEEDsWfPHjzJy8OPP/+M8IgIUCIKL2pe4OaNG8h/ko+CJ/nIysjCsSNHhNc/fvQokroloWPHToJ3VCgUMBqNwuduiku53ptYLIZYJAbLssh59AgsxyIoJAQdO3cCeZN/r8WFxbhy+RI2bvgeHy38GCaTCVarVUDmTWYT1blLF8eDe/e9jUZjNwC/ZmRkiADQ/ysMSywWIygoCAqlEu9Mmwa73Y7Cp09R39AAlmFBgL95JMGDh63jW6N9hw5C2HPdWJZlcfPGTbRq3QoWiwV6gx6du3RGdnY2Mi5mQKfT4dUxY+Du7g6LxQKKouDm5oajR47gwf0HGD5yBGJiYiCR8BiVgE6TBCRSidBvo2kacoUchLPtwnEcJFIpfHx9UPq8FPfv3Ydao0Z8mzawO+xgaIb3vBIJEpOSEBQcDJPJBJVaBR8/H4wYPRIMw8Jus6GosAhubhr4BwTA19cXFEnC4cS3WJaFXq+Hm5vbS8m967OTJAmCJKBWq+FwOJBxIQM+vt5QKlXQemhx9NBhfPv1NxgxcqSAwse3aYMD+/bDZrPhtddfR0RkBIxGI0iShEQiYc+eOStqaGjIU6lUpwGQqampzP+aUOjMC95rHR/v0blLF66hoYHw8PCAneY78RzLeyV9YyNCw8IwYeJE+Ph440XNCzgcDlitVlitVpgtZiiVSnh6ekKtViM0NBT79+5DeVkZPpj/IS6cv4DHuTnonpzM40Esi19++QWbN26CX4A/dDodcnNyoVar4R/AwwYkySfoFosFtIMGSZKQymRw12ohk0khkUggl8tBkiTkcjlOnTyJQwcPYcrUqZDKpDx8IBbBZDThy88/R3ybeHRJ7AqxWMyHUIaFzWKDw2EHQRJQKpSIiopCSEgI3N3d4eXtBZPRhGtXryImLhbXrl5DVVUlYmPj4HA4BEjBhbsZjAZ4eHogbdFiZFzMQK8+vaFQKWExm/Hp0nR0T0nGF199CalUipZRUYiNiwNN09BoNDh29BgKnz5Fq9atIZPJ8M2ar9ndP/9M9urVq3jMmDFr/yehB+qfBJCisbFxxvARwz0Su3WDzWYj8vLycPTQEYgoHi0HAHetO3z9fMGwDBx2B2w2GxiGAcuyfDkPAiXPSsAyLIxGI77fsAHrvl0LhUIBkUgMo8GAC+cv8N6GJLF82TKcPnkKtDMXmj13DhQKBTIvXoS/fwB8/HwEsFOhUIAgCGcYvo67t+8gOjpawNc4joNSpcR3a7+Dp6cnBg8ZDKPJKBQSJqMJYqkYUdExaNasGZRKJViW5cMo5fS6zrS4sbERDrsDNEMDBFBXW4uCpwWIjo2Fp6cnsrIu4drVq4iOiYHY+YCwLAu5XI7sa9lY9NFCPC8pwYqVKxAQEAipVIob12/gUlYWvl77jeCR7XY7vLy8UFhYiAf3H6Bvv37IzMjATz/+hN27duPu7TuEWCxmy8vLPd9+++2aGzdu3Bo5ciSVm5vL/VuEQo7jiNGjR5N79+7lnIxHoimiK5VK0aZNG/XJ4ycIrVbLbd+6DbW1tdA16vDgwQMsXLIIfr5+kMllaGxshN1mfykEunIrAFA7K8PCwkJcOHceUqkUBfn5ePq0AMVFxUhJTcHwkcPxODcPuTm5kEqlsNlsUKlVkPDvA1p3dxw6cAB9+vVDdEw08p88waVLl1FRVo6Skme4cf0GAKDwaSEWL10CkiQhk8lwI/sGrmdnY/iIERCJRKAoypk8ExBLxBgzZiwctAM11TWoKCtHeGQEZDIZ73k4PuRTIgoajYZP0sGBIilYbTY0b94capUKIorC9BnT8fmKlbh79y5SU1NhMplclTU4lkV5WRkIgsBH8xfA188XM96bKTwUrjzS5eXsdjvGTZgAlmGwfNkyLE5bgoiICFRVVSMsPIwoKysjt2zaLDtw4MCmtLS03LS0tCt/FpHnOI4k+EP6w3P/hzxWWloamZqayuXm5nJisZijKIp7+PAh5+pDpaWlkRcvXuQ+/PDDmt27d/c5dvSoKL5NPPHBgvnE0GHD0KFjR6hUKkhlUljMFphNZgGncRlUdVUVnuTlISAgAGqNBlqtFjGxMRg0ZAgGDByAiW9OwrgJ49E9uTvatG2HiIhwtGjZEl5eXrhw7jw6d+6MOfPmgiBJWMxmeHl5wV2rxZeff47Dhw9j65YtyMrIhK6hAWq1GhUVFQCAx7m5MOgNCI8Ix7OiYny04CPodDoQAFpGRfH4FMM3okmShNFgBMuwkMqkqKmpRu6jHIicuZcrNHIcD4K6gGCRWIyqygo8fPAQdocDNqsNIcEhiIqORsmzZ2jeooXw+jRNw9/fD0HBwSBJEj4+PtDpGrB96zZUVlSguroaNdXVSO3Z4zdVOYPUHj3AMAy+W7sOr44di9hWsaBICkq1iujVuxd7+OAhwuFwBJWUlPz08OFD8v8FOzjPnQXASSQSjiAI7tGjR5wznHL/kGG5yHocx/mr1ep5Xbt2Xdm6Veu3evbsabxx48YjhmGIzMxMcByHEydOPKAoakLr+Nben61cwcnlckIu59FuVwXnauq6DkAmkyE7+xp+3LETjx/noX1Ce7i5uQmVo1QqgYenh1BR+gf4Q6PRwGKxgGUZtGzREufPn4dSpcLwkcP5BBgkbDYbwsPDcevWLZw/ew4tW0Zh+PDhWJi2GKNeHY2AgADcu3cfNE2DYRg01NeDA9CyZQs8L3mOp0+fYt/efbhz+w7CIyOE1o5cJue9E8NCqVJh988/48SJkwgKCoLDbgdBkEJeJ5PLeLiAJNC8eXMEBwehUdcIm9WKnEc5cHN3w7PiZ6h58QLNmjXj2RwkCW8fb3To2AEDBw/CkKGvYPiIEXB3d8flS5dhMplQXFyMhA4JCAkJEQzS1Sft3KUL9u/dB6vNgnBno95ms0KhUODGjRuESqEkip89+5amaeJvGQfHcWRqairbaG1sKRfL07t27bq4devWo0eOHFlx/vz5IiennvsvhcK0tDQyIyOD5DjOf/To0RnHjx+PJCkKarUaLMN0GTRoUO99+/ZNGT16NLlnzx4uBzmiVmQrqnV8G1AkhXpDvdCXE4vFUCgVAobjghjEYjFOnTiF27dvAwCel5SiecsWcNgdgut3NV4JgoDFbAFB8pgUx3Jw0A4o5HJkX7uG9Wu/w7szpsHO8PSXnJwc0A4Hvt+8EfFt2kClVsFitsDhcGDk6FFo07YNPk3/BLUvatG5axe0bNkS1dXVePjgAUaOHgWNxg1WqwViJz3Y4XAAJKD10KKmugbVVdXo2LkT9Ho9bly/DrFYgqHDhkKt4VkcLMMn5VKZFEajESKRGPHx8eAA6BoacPfOHaT0SMXZM2eQcfEioqKj4eHhAXAQoAgXDPLauNfRqXNn3LxxAy9qXiAkJAQSiURgUBAEAcYJ0ShVKjTq9PDQamG1WOHn64fyigru+bNnpKfWI4fh4Yy/OdhBEARz5cqVDiMHjbxw/cZ1la+fL+rr6iGTyfqMGDHio3379q1s166d+Pbt246/27DS09NJAPQrr7yy8MiRI5GjRo+y9u7TRyJXKLgjhw+zWRcz31q+fPnuvXv3ZhAEwRIkaY+OjmauZ2fj9fHjhJKapmkhhzGbzEJrgyAIXLxwAXdu3xawq7y8PPTp1wcOOF7Ct5piXADAgRO+zrB8D2///n0YPnIEPDw9IBKJUF5ejgmTJiImNgb6Rj30jXohr2tsbESz0FCs3/g9Fn20EAVP8hEREYGL5y9g8tQpiGvdiu/TOSkzdrtdeA8Mw4CiKAQHByMiIgIikQhnz57FyRMnMPrV0VAqlS/1FV0PEsMwAiDr8solJSUICQmBQqGAv78/rFYr6uvqofXUCl6eIAhUVVVBLBajZ69eYDkWFy9cQNCzEnTo1FF4b4TzvjQLbYaKinKIKTGssOLmjRvcN19/A4lEqmvfvn3asWPHyFGjRmHv3r1/SPysqakhOI5TTpky5Yuz586qFi5eZO8/cIDIYrFy69etY0+eOLGif//+OHHixEqn/dB/jUP1h1bLcRyzbPnyj86cOfPuu9On0emffipr17496e/vT7Vr346w2qxMXV3d6wRBMBzHeX23bt08q9Ua/Dg3l/nsk0/JpwVP+f6XWAS5guc3ubm74e6dO/ji888xc9p0LF/2GWw2G0QiMd6aMhkpqSmoq6uDSCSCSCSCWCwWEOWXPr0zlLqYpRzHoVGnR2VlBYKCglBUWIRGnQ7hYeFoqG8Ax3FCwuuCR8xmM8QSCea+PxcOhwN3bt9BVFQUWrRsibraOqFf2ZQDRZIkbFab0CUwm80wGo1ITExEZGQEbt644Rrd//2JNTE0SkSBoRmsX7sOWzZtgp+/v2CMHDhYzVYB22JZlq8wnSS+0ufPsfzTz/DBvPdRU10DkVgkGCDHckhMSkLe4zyYzCYUFRbhg3nvc49zc8n27dvXLF269AkAds+ePexfOXcyMzOTBqDKyspKSUhI4Ma8NlYiEolId3c36rPln4nenTndcfXqlRVjx45dAIB2ja79GY/lyvylv+zataRL1y6YOes9qr6uHhzHwcvLCyRBUY2NjcSOH37ov3DhwkupqanBeXl5zdy1WsTGxSLj4kVkZmTCx8cbb0yaiHETxvMHKRbDx88X2dey0VBfDwCIj4/HO9OnoVv3brDb7dDr9WjUNYJhGaGH6OXtBaPBKFRCrpuuVCghV8gF7Gv1V6vxrPgZykrL0Kdf35coO797okgSLM3AZrODZTm8eFEDESUSDLCpp/wtZvfbSpZhGMhlCrhrtb97CFzhjCRJUCIKBPiQfvrUKTx58gRSqRQWs5lPMZyYlslsgkjCh2DOWXUzDAO1Wo0LFy6AZVkYDAacPHEC09+bgZrqGuF9yeVyGE0m5D7OxdnTZ2C1Wkk/fz82IyOjRd++fc9yHDeAIAij0xi535w7ZDIZEhMT08vLy7mVX37B0TRNuAy8Qacj3n7nHVFleSWTmZGxrEqn2+Pn7l7kysXxJwYsQRAEHj161PDK0GGw2+zCDbLb7YiKiiIGDh6MwKAgv2XLliVlZGQ0G/fGBOa779dj9TdfY+GSxXBz06C6uhrnzp6FwWCA0WhESUkJ/Pz8MHzEcPj5+SEtfSm27dyBLl278Hx2mw0ymQwKpQIZFy7ijdfHY/zY15FxIQMenp4C+U44MIpEt+RkHoNSKpGbk4N1367F8FEjEBsX+1II+yPsTSwRo7qqCoUFBUjt0QOZGZm4eP4iPD09IRKLf+d5aJoW+p8uA6JICjpdAzw8tOjYqZPQTRBQf/ChHwBe1LxARUUFbt+6hcqKSoG28/DhQ3h4eECpVEKtVkOj0cDDwwPPnj3Dr7t2I+PiRbAsg7y8POzbsxddkxKh1Wrx446duH3zFtzd3QXv1lBfDxLAjHem4dfdv8DhcMDhoMngkBA6Ozs7ccyYMdM4juNGjx5N/tZbcRzHjX117OanT5++vfLLL7jmLZqTLl6bC2jWGwxEj149GY7jUJiTMwEAAgICqD+dYzkPS/Xo0UP0H9BfILs5HA64a90xecpkqNRqbtFHH7H19Q3EK0NfoQwGAwiCQFK3JBzctx86nQ7e3t64fes23NzcIJVJUfqcJ7d9t2E9omJiUFxUCJlcDo1GA5qmIRaLIZVKcf36dbx48QJarRYfz1+A69euYeDgQYhs3hwMw3szsVgMiVgMs9mMx48fQywWI+2TdDRv3lwIqX/rwWEYBmqNBpSIgr+fP2bNno0ftm9HfUM92rVrh6DgoJdYEq4wp1arYTabQdM0KBGFoKAgNDbq4XDwjASHwyEUJzabDc+KnyGkWYjTIwGt4uKQfe0ajEYjuiYmYvOmTaBpGoGBgTy4StOoqa7G3l/3wGAwAAA6dOwIuVyG4qIifLdhPbIys7By+XLMeW821qz9Bi1btoTRaESPXj3h5+eHQwcPoXtKMvz8/HDi2HGcOHaMtDscLEVRE0Qi0cpFixZxTTUy0tPT6VWrVn168vSpye/P/9Deq3cvSX19/UsVvUQigbubG3fuzFmKJAjExMTsAICKigrmTxmWS7JnyJAhOXt++bVzfHw816VrV8JVhXAcB7vDDpPJSBAkScmkUigVCogoPi/KeZQDXz8/9O3fzxnadIiNjYXNZoObxg2enh7gANy/dw++fr788ITTUCrKK/Dt118jKyMTYrEYySkpuHHjOnb9vAu7ft6F5StXYPTYV2G32VFQUIAd238ASZI8i1OpRHybeDTqG4XQ4PIsTVkTrmSapEhIZVK4ubvDYXcgIDAAbdu1xemTp5CVkYHOXbrg1bFjBPDySd4T/LJ7N0aNHg1fP18BOJVKeMLe9WvZ6NWnN5RKJQDAYDCgqLAIoaGhkMv5kE0QBGxWG3JzcmEymdCyZQtkZmRgzarVPECs1kCtUaOivBxw4mlWqxXDhg9Dz969sOG79Zj85lsIDAyASCxGdXU1vvt2HdauXyewUzt37YLOXbpAJpeBZVl0T+6OsPAwrFm1mnjw4IGYpmkFQRBm55Q6l56eThAEgU8//TS8R6+ezCvDhpIvamoEz+zkhLH19fXc8s+WsydPnBD3799/vlarLR41ahSVnp7O/JnknTt27BhFEIS1d+/eF60WC9atXceanegwwzBgnUZgNBqR8/ARomKieVqLEx4wGA2YMWsmhgx9BRzHCfQYhuY9jbePD65nZ0OukMPd3Z3nKjmZmA8fPsS5s+cQHh4Oh8OBQwcPoqK8AiqVCrFxsVj37VpsWLceG75bj9dGj0FZWRk6dOyIzdu2wmg0IvtaNjy9vAQAVqVWO3MVTnjvFEXB3WlM3327DiXFz3DixHGcPXMGdrsDca3i0G9Af1RVVuGbNV/j7p27+GX3L3h9zFjkPc6DXCGH3W4XEmeLxYzQ0FAUFBTggznzcP7sOez55Ve8PmYsCp8+hV+AHywWnqYjEonw4P59dOzUCQqlEl98/gV0Oh3Po/f1xY6fduLk6VPoltwdw0YMR7fu3ZD+6SfCvZz/0QIMHzEMN2/cBO30jG3atuVReyfe53A44KB5SrbBYEBdXR2mvvM2+dr4cdzjx48j+/Xrd5LjODVBEC+p57AsyxEkxVeYHAeapgVO3RcrPydfHTGKOn3ipDg1NfXDXbt2fZGcnCz6a0g89UcV4YULF+hVq1bNWbN6zTKlSsXMnPWeKDAoCA6Hgz8wZ2g4feo0rl29iqlvT0Wz0GZgaEbggXt7eyPzYgakEimSuncDAQJyhRzggEZdI7Iys5DaI5V3tQLDQIKa6hqcPnkKtbW1aBnVEm9MnIj4Nm3Qu29fzF+wAAGBgVjx2QpcvXIF3bp3R31dHXr16Y1x48eDYVisWbUKYaGhQo519tRp3LlzB3FxcVAqlZDKZNDpdLiRfR2rv1qFhvp6eHl7IywiHL369EZ823g0Cw1F9rVsdO2WhNLS51iycBEyMzIQ1yoOy5YvR0BAwEtJPEHwnjE+Ph4Omsb2rdtwYN9+kCSJvLwn6JqYiICAAMjlclRWVODatWwolEpcuXQJffr2wYxZ74EkSdy7exdVVZXIzMhE6fPnmDNvLkiSRJekrkLbx2KxoEvXrkhISIDWwwNh4WHo268vvH19wGNUHAiCFOhDrvfJMAyio6KJE8eP04WFhWGPHz9ufPTo0eWLFy+KJk6ciIyMDPbTTz9N2Pvrnu5e3t50u4T2JAEQZpOZ+3De+8T5s+dyZs6ceXngwIEzV61a9RPHcVRJSQnzp5D3tLQ0cv369SzLsmEzZsw4SohI4qs1q4lmoc0IPqlWgnSyJMtKS1FdUw0CBERiMbp16war1QqT0QijyYia6ho8efIEQ4a+AqlMyieAFAmNRoOsrCxs3bwZIopCckoKbHae8qtSqfDjjp14cP8BBg0ehDXffotOnTuhY6dOCAoKhtVsQYdOHcFx/CDEgIEDUVFRgVeGDYOHhwd69OgBu82OtCVLUPqcZ3f+sG07jh05irzHeaAZBhfPX8D6deuh0zWgf/8BGPPaWNy6dQv9B/SHp5cX7DYbvL29UVVZjc8++RQVFZXQ6XTo178fVq1ZA7VGLVCUm879chwHkiDQpm1b9B/YH/Hx8Zgzby7yn+Rhw3cbQBAEnpeU4NatW/Dw0GL1V19hzNixWLZiOZqFhaJP3z7Q6Rpx7MhRPC0ogEQiQdeuiTx1OyREqBhdCX+z0GZI6paE1B6pcHN3g9FgBEmRPPW5uhoMzcDDw0PI91y50pFDh1FbW8tFR0eH5OfnrysqKuIyMzPZUaNGUV9//fXFhw/uh+z44Yf29fX1hJenF7Zv3cadOnmSSEpKerJjx45ZHTp0uOVUQWT+NPLuzO7ZM2fOjKmpqSHmffg+7ebmJs7KzMTTp4XgGAatWrdG23btUFhUBC8vb3ww/0N8sXIlfv3lVwweMhgenp7YvWs3njx5go8WfgStVgur1cqX9ww/JWO32eBwOLDx+42wOxx4+913IJFIsOrLr7D7513w9/fHvA8+gEQsRkNDA0iCr0pEEhFMJiNaRkVh/brvcOjgISxawjddi4uL8f2G73Hl8mUhOe/bvy+GDh+KC+fPY8nCxcjKzISXtzeWffYZErslgSJJFBcXQ9egg0qlAuvEkkwmI3r16YUftm9H/pMnIAgCPXv3hkwhh74JN70pg5ZnyHKw2W1oqOd7kjKZDEs/SceAfgOwcvkKfvhk/z7kPMqBt7c3Zs+bA71BD9pBQywRY9qMaci8eBGVVZWorKzEhvXfITYuDmHhYXBFDBfkYjabhbnC0uel+CRtKRw0jeiYaIDj4KBpDBo8GG3btRVaP9s2bxX6pBzHUU0fjr1797IEQRAymWzS+++/b/7mm2+G7vrpZ7++/fsRPXv1wtOnT7u1bNnyydSpU9/bvHnz2pEjR/7NRrbor1CNKYIgoG/U48uVn+PUqVMIDAyE1WrDzh07kdIjFX379UVdbR20nh6Y+s7b2LF9B9zd3ZCckoLi4mK8qH0BLy/vl55uV/nu4eEh0Iq3b92GS1lZEIvFaKhvQP+BA1BXWwtKRMFqs0Is4pu8LMuCtfNg4d5f98But6NDhw5o3bo1CgoKMO3td8CwDEaPGYNRo0chJTUVGjcNrFYrXh0zBsVFz7Bj+3b0H9Afvfv0RmlpKU+ZJgiIRSIQBPmXKWOOr+jeefcdLPhwPhwOHqB0hZff9TylUnDOz1fy7BkunL+AlNRUSCQSXLt6FWaTSVCKuXXzFnQ6HUTivzSqCfC/00WRZhn+9e/duYvHuY+h1Wox+e0psNlsQmhzlf8URQEEUFZWhnYJ7dGiRQt4enqitrYWiz76GNNmTMfrE8Zj76978MP27YiIjGQb6utFHMf97HA4MGrUKNJpIJzz84u/+uqr6R06dPCpqKwcOXnqFEYmlVEcwHy9ejVx+vTpL69du3awc+fOZX+L3/WSYbnKxvj4+P0BAQGfrFy+QkTTNLfss8+IromJYFgWe/fswfq169CxY0dQFIUzp06jdevWGPPaWMjkMpQ8L0FdXR1Ymk/k5RK5AA+IRCKQJInMjEyBESCVSvG04CkIksAXX30FhVyOB/cfgmVYuHu6o7GxESXPSkCJKERFRTnZpBcBAGVlpfzI2PwFUKlU2P7jDnh7ewsDHFarVZgf7NylM3Zs345dP/2M5ORkJKemwmwywU2jAQfg3t276D+gP3SNOtisdtTW1qFN27ZISkrChQsXsHXzFnTo0BH+AX5C/9KV3N6/dw8bN2xEYGAglColuicnIyY2BnmP87Bm1Wqh9+fr64vPV65E8xbNUfr8OX7csRPTZkyHyWyGRCzGyuUrBPmmsa+9Bg4cftm1Gz6+PvzU928wOYIgYLfbERoaik+WfQqVRo3w8HC+t2lzIPtaNkAAjTodnMUX+6y4mGrfvv21zZs3f7N3715iz549rOt1ly5dSgBwWCyW5r179x7ZoUMC1Go19aLmBZRKJfXqmDGOB/fvizMzM18FsGrq1KnUpk2b/t+GlZ6ezo4aNYoKCgp6PHXq1E+vX7/+cb8B/YnklBSquroaEokEgwcPxu6fd+HwocOQSCR4+OABxBIJWrduhZmzZsHNzQ1t27XBTzt/wunTp9C3Xz8oFAoolAo47A58s+ZrnDl9GiqVCvX19cLYPcdySFu0CMEhIVjzzTdQqVXY/fMuPHv2DKFhoTh+/Diio6Lx7NkzEAQBL29vZGZkYe7sOXj08CE2b98KrVaLFy9evISeuzxj9tVrYFkW7dq3xzdff407t+8IHigoJBg7tm9Hy6iW0Gq1QpUmEokQHhmBCxcuoKKiHOPGjsX4iW+AdjigUqkQExOLxkYdlqYtRXJyMnr06onIyEiIxSJs+n4jvt+wARazBT4+PvhgwXy0T2iPu3fu8toPnTtj/brvUFZait59+2D/vv04deIkAGDk6JGY/f4cHD18FD4+PkhMSoLNav1DsNeFx8W3bYOqyioYjUYY9AbcuX0HrwwbiujoaFSWVyC1Rw+cPnWarX3xQrR27drl7u7uDWlpaSKCIP6o18c6HA6IJRJOLBITLiIiSRGcM1ej/m6i3969e1kAxI4dO9Kio6LfYRjGhwPHsSxLuLyOUqnEk7w8UBSF8W9MQE11NU6fOo23J0/BlLen4rXXX8eD+w+xYtlyHDtyDAAHmUyOmupqPHv2jGc7KJT4cMEChIWHoqqqGvfv3sPuXbtQkF8AuUyOo4ePYtvWrVi7/jtEtohE5y5d8M6UqcL0cO2LFwCAkydOQCKRwMvTC1abFSKR6CUeuUKhwKWsS/j5xx8x9rXX0KVrV7w3Ywbq6+oxe+4cVFZVwVJZAdpBY+GCj/H5l19AoVAIPPgnT54gIjICK7/4HLPfm40vVqwU7lVS926oqKhAZUUFRowcgVbOsLzqq6/wODcXvXv3gUwmw5jXxqJldBSMBgMGDxkMjUaNM6fOYPKUKdi+bRuWLFrMj/v36gWxRILXxo2D2WSGWCyCUqUUUoG/BmQTBAGDwQC5QoGysjJcvXwVQ4cNhaenJxoaGgCSAEVRGD5yBDau34Bnz54pOI4jli5d+lviAecUAa709vK6kpWRmTh02DC7n5+fiCBJ7qeffiRtVhvbqlWrQwDg7+/P/L3sBs5sNssnTJjA7d+3D7k5uYiJiQHLsjh39ixqaqrh7e2NL776El0Su8JisWDchAk4uH8/1n27Fi9evEDLli3x4P59PLh/H/7+/iBIEnFxsejUpTMsFgtee+01tGoTD5vViujYWPTt1xd9+vXB0iVp2L9vH27dvIUvV69Ci6gWaKhvQHCzYHy3cQPGjXkNHp6eGP/GeH5o1WrFo4ePUFlZidCwUNAELZDmXKyJ79dvQGBQEIYNG4aFH3+MsPBwbN66Bf6B/mAZFkWFRTh25Cg2b9qEb77+GpPeehOGRj327d2La1euIq5VK9y8cRMBAQGoqeaF4vr07YPRr74Kg8GAjd9/j4kT3sC69d/Bz98fvXr1Qvqnn8Db21vIz3QNDSBJEnV1dYhr1QpXLl9BSLMQfLlmFRx2O1iWRf6TfJw7exYOB0/bbt26NRp1jTh04CAmvjkJDfX1oP6gm8CwDK5euYoXNTXIy32Mt6ZOQbPQZnB1QlzUb4lEDIZhYDQaWYIguLS0tN+du4+PD0cQhPn69esfzJs778Lc2XNk/v7+MBj0sJgtSElJWTpo0KD8vwaM/hlqMieTyeRmi4Wb894sRDSPBMuweJKXB7vNjjcmTkRityRUV1dDJBIhrlUcOnXuhKRu3TF39mwhwZz6ztvCyLuXlxcUSoVQOjc2NPAgkNUKhmHQKj4eH8z/EG9Pnop+/fuhTbs2qK/jw6Vep0dUVBSSU1IQHRONocOHob6uHh4eHqAdNEqelaD2RS2kMr5hq1KpIJVK8esvv+Lhg4egaQeWLFkMd60WH8z/EN4+3mio5w87KDgIEya+gZbRLXH/3gN8sjQdjx48FG7Evbt38fDBAwF0TUxKwvg3JsBitkCr1WLW7Nn4ZOknyMnJQYdOneDn7we73Y6GhgYhJLvKfalUiuclz9FQz/8/mUSK+he1uHPnDooKi5DzKAehzW4goVMHBAUFYfioEfh+/QYMGjJYoEE3bX5rNBpcu3oN3379NQgQ2LDpe8S1agWDwQCJRAKNRgO9Xg+5XI7zZ89DJpMhISEBAJCSkoKmM4ZOCjpmzpwp7dSp07WysrIua9asmclxXLuGhgZ9SEjI55988skJjuMIZ2T7u4h+LndoVyqVh2Qy2QRvHx9rQECA5NHDR6TNZoOvry/69OvDVzfO0GOxWGAymTBg0ABkZ1/D3l/3IDk5BaNGj4bdOVdYV1cHhmUExRWSejlUGw0GhIaFISQkBHa7AxazRaDNSKQSvKipQXV1FXr17Y3amhf891gsEIvFCI8Mh9FohMPO889zHuXg9MlTiIqOwsYtm/CsuBhnz5xBSo8eaB3fGrW1tQJsYLfbQVIkWse3QceOnXDjxg2s/fpblJQ8Q1hYGMaMHQsfXx/kPMqB1WJB16SusFqswvSPRqPBoMGDUF5eAXAcyp6X8n01D63AhefRLr6dcykrC92Su0GpVKKxsRF19fXo2rUrBg4eDKPRALvVhtq6Opw/ew6hzUJht9uxacNGLFq6BEajwSnhxEGhUKCivAIrly9Ho64Rr48fh7bt2gmfjWVZyOQyECSBHT/swInjx9GpUyc0a9aM/Gt6sU58igGAoKCgeyRJviWT8a0hZ0vvT036/KHHcrpDjuO4pfn5+T3v378fWFlRAZqmObFEQny0aCF8/fxgMpn+ooPg/Ntqs6J3n97Y88uv8PX3ExgRrtHxpryopgmoWCwGSVEw6A34bOUKGI1GPC14irDwMNA0DZlMhp9//Ak1NTVo2TKKhyLEYqGf5cqnWJYF7aDx7ddfIyYmhjdshx2JSYno1r07fti2HQ8fPEREZIQAhVAUBaPRCKvFAovZjE6dOiG/fz9czsrCu9OnCVhcckqyMMbedGzLarWiefPm2L9/H86eOQuaptE1qatgTC7volQqUfr8OQICA9A6Ph719TwVqWXLlhBLxHA47M5CRwkfP1/kP8nHl198CYfDgZ9+/BEKhQK9+vQGJaJAkRRomsayTz5FcVGxcxCFZ7o2HbYAgJ92/oiSkhJ0S+mO4oIiXL582QSAzMjI+C0F3WvdunVTwHFt6hsaGhISElYPHDgw32w2k/+UYYrc3FzOSaZvyM/PP6jT6Vg3NzfNlStXfELDQjHvg/dhcUoWuhRlhJtstkIkFvFaVBoNfHy8IZXKeMqJVCokxk3FKhmagcloRFlpKQiCgEajgZubG19O2+w8x8hohEgkQouWLSEWi+Dr5weFQgHKOXpFEAQcdgca9Y2oq6uDw+7ApMlvgWF4gpzJZIKPjw9YlkVW1iUkdEwAy7CCroPFbBFwKYlEgvx8PmmPjIwUGAYuGcnfTi8zDAN3rTsMBiNOnjiBLl27ICIyUuC/MwwDhVKJirJyPH6ch5jYWDA0r+XgrnWHWCwWiH78SBkLhmbxJO8JrFYr/P39oVapcPrUKZw5fRq3b93GubNn8OOOH/G8pAQKhQIxsbEYPWY03z2w20DTNGxWGyrKK3Dl8mW8O30a4tu25Q7u308+fvwYFRUV+zmOIydOnChKT0/Ho0ePoiZPnnx5//79wx7mPIq9ln0tISMj491JkyblZ2dnP5oyZYpo586dzJ8dz/9b1GTW6R6LAcx1d3fHmDFjtp08dXLSk7wndKvWrUR6vR4czQlAnYN2wKg3giRI9OzZkw9/9XUwmy1OjhOv0U7gZTmgRp0Ox44eg6+fHxITEwVxM7lSDo1aI4yYJXRIAE3T2PvrXuz+eRf69e+Htm3bwWa3QalUwmQ2Cd7Ly8sbUqlUADZdTT2SJJGY2BVkE0DUNSAhlfGaDzTDQC6X40neE8THxws//9e4XS5oQq9vxKNHj3DmzFl06tIZcrkcZrMZ7lp35D/Jx9S3pmDgoAFon9AeJqMJJMUn80FBQcIDxnEcpDIpnjx+Aj9/P6R/+omTrWrCkyf5KCwsRExMDEiCwLmz51BeXoaxr7+OuFZx0Kg1qKqsEmg+YrFYMEyKohAcFESOf2M8s3/v/pFbtmxZ9eabb97JzMyEVCrF2rVrv7p+40bQp8s+tUdERlA0TbOfr/xCvG/fvk0MwxwkCMK+adMml24/92fkHfH/Mq7k5GSRTqcjRo4c+VFDfUPtwo8+Jp+XPOfc3N3hcDjQUN8AXaOOJwQ6hzeMRiOfW7EcVn/1FXbv2sUrqtgdAgvCZrWhrrYOEqkULaOj4Obmxs/yOVmfHPuy3qaLM56c0h0hzUIgosS8tzFZBJ6Yh9YDbm5uyLx4Effu3oVSxQ+Wumu1uHv7DjZv3MwrBjKs0wg5aDQaKJQK1NTUYMP69fhy5UqYTGYUFORDr9e/RLn5o3JfJpUiNzcXx44eQ2yrOBQ+LcCc92ajvr4ebm7ueJzzGNPffhfu7u4IDQ0TCIguSYGD+w8AHKBUKvlBWIZniAYFBcFsNsNiNoMgSHTu0hlvvvUmWrZsiZZRUZg56z0sTktDTCwvveRizAJ/CYNSqRQ2ux0GvR61L2oJihJxJElK2rZtm5yZmdlu48aNP78z9Z2jO3fu7P/qmFfZ+DZtJCajiSJJSjx7zmxWb9Ar2rdvf+Xbb78ex3GczJkiEf/wwKoz9oIgCI5l2Whvb29ZcVERN3PadOKzlSsQ0iwElIiCQq4ARVGwOoE8F+vQ4XCgsrIKgcFB0DXqeM6WhFfAcxkK7aDhofVAVSXfI1OqlPygqDPkuJ5A17+9vL0xYeJEWExmnrFJkXxLBLzxOewO9O3fD+Vl5Wioa4BcIcepEyewcMHH6Nu/H/z8/SGWSHgxW5MJZaVlyM3JweHDh1HwJB9WqxUXLlzEGxMnwM3N7Xfan797OikKRw4fgVQqxWfLl8NsMePr1WswZdJbCAgMxNOCAvTo1RMz33sPFEVBb9Dj+/UbYDab0KZtO1y7chXl5eVon5AAiViMuFat+KENF7TgzEEpioLVYhV0KVzNZbvNBqVSIWCMer1eQOpZlkHuo0eQSSRoFhqK+/fuicrKyrh58+atLi8vFxYSDBw8CL179ybr6uogcno6pVJJpi1dSu75dU/Cl1+u+vHkydOTOY4bkJKSYk9LS2N/S0f+u0fsMzIyqJKSEra4uHhkVVXVII7jGKvVQsXExsLX1wdGowk0Q0OlVAmKLq5hh5qaGjQLbYaRo0aBIp1sRIaFSCSCm7sbRGK+qlSr1PDy9kZZWSk2btgITy8v+Pr6CsJpJEkK+qUP7t1HcVExNG4aiCViMDQjJO1SqQQqtRoxsbEIDAoCy7IoLS3FB3PnISo6GouXLoHZbMbF8+eRcfEi7t+/L7BBb2RfR2VlJRiGwYgRI9C3b98/YDL8sXYF7aBx69YthIeFI75tWwwYOBDJKckICg7Cq2PGYNCQwUIS7+7mDpIkUVDwFK8MewUtW7bE45zHyL6WjW1btuH8ubOoqqyCUqlAWHg4HHY73Nx5b06JKDAsI+B0ZrPZqWCjBEHwXQaJRMJLShIkjAYT4lq1QnJqCqJjYtC6TWvU1+uIa1evYvjIEdzMWe8xg4cM4Tp17kSy7F8eYJdT8PPzQ89evdiw8HB6965d4UWFRZ1OnDixQ6fTiSorK7l/yLBKSkpIAKzZbI7X6/UDRWIR++ny5VSXLl1gNvMc78rKSnj7eAsiY64KkJeadsDDw+OlsSiHwwGJVCL0DCUyfhZPLpeDoijExMRAJBLxMo9yGaxWK25cv84PV3h5ofBpIW7dvIkWLVoIWxr4iWuZkGi7FGK0HlrEx8ejbft2cHN3w+6fdyEzIwOREZEIDQ2Fj48PvLy80KZtG2i1HkjpkYqU1BTB+/6ty9UzjIqKgkwmx+ZNmxAVFYXy8jJcOH8BVosVYWGh0Go9hGSeZVkEBATg8qXL2L5lG65euYL79+/DZrNh7ry5qH3xAhkXLyIrKwueHp7o0LEjQOAlKW6GZoRRMxe+ZbVYwbH8A221WMGw/PdENI+AVMYXUG5ubmjXrh0GDBqIjh07EjRNkzRNky71GyENcc44MAwDq9VKREVFURKJxPHdd+ubjx0zJu/UqVMP2rdvL66srGT/y4aVlpZGZmZmssuWLet07erVAfFt2rKT3pxE6XQ6waPI5XKoVWrIFPwEsFwuh0Qigbe3t1PUrBGenp4C+ayplLRLXEOh4Ico8vPz0TUxkdf5tNugUqpw/Ngx0DSDrkmJkMvlaNO2DYwGI77fsB7ZV6+huKgI3VOSBX0pV/efICAApu7u7ti8cROelzzHlKlTecFYii/bXVVrdEw0AgIC/pRRNTUum82G2LhYlJWVYeuWrbh54yYkYgmKn/F0nsjmzREVFfWSca3/bh3KSsuQkJCAkJBgPidUKjFw0GCYLWaUFD9DybNnGDp8GMQSsZASKBQK5D1+jD2//IqOnTs7NfEJoRBxhUoCxF9WpTQxGFf+2lR4zvVZ5Qo5P4lOM0KOS5IkL0UeF0vWvahlz5w5M3rKlCl5hw8ffjBq1Kg/FBn5U3v3UlJSAAA9evTgFEqlc3ScBOM8EJVKjWtXr2L/vn0gCfKlG261WhEaGobysnI8fvyYH/Ey6IWDZDn2pQNM6NABZaVlyLiYAbFYDC9vLzwreYanBU/RPbk77Haey2U0mZDUPQkval7g3Nlz2L1rN86cOg0vL6+XaC00zaBR1wiLxcIzAcJC8eqYV4Wb1ZRA52x3COH877kIgoDZbMarY8ZgzNgxmDtvLt6dPg3z3n8fr417HZ8tW4anT59CLBZDJpPhzOnTKCstw7fr1uLb79bhm3Vr8eXqVTh29Ch+2LYNk6dMgbePD6RS6V/E5JzvUSaTwWqxorCwEDTt+MOZy9/Se1x/TEYTdA06YbLJzc1N+B0URcFitsCgNwg/63ot55wn8flXX5AdOnZkzp49+8vDhw/77N27l/mjtcl/10JHi8UiksvluHXzJoqLi+EfEAAfHx8UFRXy/b1bt3D75i2Bfy1UCGIRrl6+gmXpn2DXTz/j7bemYO6s2bh/7z6Uir9MDrs2U7w7nRdvK33+HIf2H8RHHy5AVmbW76gjBAhhcAEAvvz8C5w6eQoymUwAPs0m80vS2AqlQhD7/22117To+MMk3ekFm8oE/PZAeY8zCAHOiZv6+nr06dMHEeHh2LJpM+RyOfR6Pfbt3YdpM6aj/8ABqK+vR0NDA4a8MgTvf/gBmrdoga5du6Jfv34oLi7mteplctidyw10DTrs/XUvioqKUF5WLnwe12eUSCRQqVR8tatQCIZjNBgFUJthGD5xl8ug1qjh4ekBjZvmJWMCAUGb313rDqlUCqvVSixJT2NtNhtmzJjRg+M44tixY8Q/ZFgsyzaKxWLo9XrivRkz8fGCBZj/wYeYNOEN0DSN0WNeRUZGhjBb57r5NE1j0JBBAICamhp07NgJhYWFmP/BB3ic+xgKhUJQMbbZbIiJjcGEiRPQLDQUv+zajZJnz1BTU43169ZBIecBVrlMhnt376Lg6VMMGjIYPXvxG7femz4Dkye9hUnj38Cijxairq4OXt5e0Gg00Ol0PEt11+6XDPLPXCqVCmq1mkfGnX/+aLzMtbTgpZ4eTUMqkeLu3TswmUzYtnWLkxExUpC9JEkSer0evXr3QdfERDwreYaUnqlo3qI5Fi74CCaTCQGBgTAYDJgxbRouXcqCQd+IRR9/jOrqari5ucFms0GhUECj0SAzIwMHDhxAdvY1PCt+BpvVJlCUXA8JQzMvVZhNyZj82D4BiqI4vwA/4esWiwW+vn7iiOaRbGBAwLsAZLdv33b8FoL4UznWjh07WADYtm3bwzNnzozJz8/3kctkrIOmCYIgMHzkCMTGxuL4sWNI6tYNkc0jQRAQPAxN02jeogWaN2+Odd+uxevjxiEmJgaXsi6hrrYOffr15RVkaNbZ2uBV/jw8PRAUFIwzp09DLBbj0cOHIAgCnTp15gVFTp7E7Vu38MPOHeg/oD+qq6qRl5eHqspKeHl74/69e8jKzEJhYSHu3buH+rp6RMdE86KzdbVo3br1X6Wj/NYbubyga/yfoihB8vu33+v6w7Is1Go1CgsLcWD/ftTX1ePm9Rs4dfIU5sybg4QOHYScy+WJq6sq4entBXCAxs0NvXr3wvlz57Drp5/x4P4DfLfuO1RWVmLJJ0sxeswY5Dx8hN0/70Jcq1aIiY0FzdD49JNPcO3KVURGRkImk8NsNCHjYgbKK8oRHR0tKAlyDAexVPzSmJcr39RoNNi/fz+79ptvyajoKCYiIoI0Go38OhgH7dix/QeRSqU6MXbs2F9yc3PJ0aNHs/8lRb/k5GTRpEmTmJYtWxpLS0uHLly8iJ41ZzaVmJSILomJKMgvwKWsS5j69tsgKRIUJXoZ3DSbERUbg9LnJTh+/AQAoLi4GM+Ki2Gz2eDuroXFYuHVjiUSoZ0TERmBG9ev49UxY2AymZD/5AnGvDaWf3L8fHHi2HFUVlUiNTUVbdu1xcULFwAAUdFRkEgkKHz6FPlP8pHz6BHemvwWJjo3V+zftx9mowlR0VGCus3fMiyXkEnTJ/u3T/tvn3ypVIq83MdYs2a1QGGpqqrC+DcmYNr06YJWaNMCoFHXKHhThua58J27doG3F18EderSGdOmT0NcXBy8fbzRp29fPM59jM0bN+LunTvY9fMuqFRKrPn2G3Tr3h1RUVGIiIxAeEQEHty/D71eD19fX2GqXCwRv+R5JVIJKIrCrp9+wratWwmKJGvOnDqtbhYe5oiLjeUsFgu96KOPJVWVVbqZM2eOi4+Pr4mNjSV/m8D/aXHbzMxMluM4YvLkyUPkcjlax8eTrkTXoNej7HkpQkKCoVKr0VBXDy8fr5dG0flenh2hzcJw+OBhlJWWYszYseia2BURzSN5HjwBQa+UIAjIFQrU19ZCoVDC19cXZaWlmDV3NgiSD5mhYaH4cvVXmDRhEpKSktCjZy/EtWqFY0eP4uqly5gxexbiWsXh3Jmz6JrYFe0TElBeXg4/Pz/07deXZ0I4c4n/l8f6e6UzXY3t9evXw9PDE0NeeQV7f90DLy8vTJ46BWaL+XeGKpVKERjE52Yu9SmO5SAWiZHYLUlYVHDowEFcu3oNAIeomBh0S+4Og8EAjUaDUaNHI7VHKjhwqK+vF4RG1Go1Xnv9dVy6dAk5jx6hpKQE7dq3R7v27YTUhZ8MVyMzI5PZtmUrN+SVV9bt27dv6fDhw/csX/ppn0N796PmRQ0MeoNuxIgRvcaPH5/719QB/x7VZBYAyTJsamBQEDw8PYkXL2pAEgQkTk31ivIKWJ1DmY2NjXBzcxMSedI5OPA47zE8vbyw4vMV6J6cLOiaCzABRQry3SaTCR/P/wgdO3WE1EndSO3RAxazme/N6fTokpiINm3jcf7cefTt1w8cx6Jtu3ZI/zQdkc2bw2yx4LXXX4e3rzc48BCHXq+HiKIQGBb4kr7Db6XBmx64CyL5e6pEh53Ps9y1WixNT4fdbkd+3hNoNG6wWHhNBDi1EV0FgYeHx0tlfnVNNa5fy0bPXr0gk8qQvmIpjh89hj59+0Dj5oasjEw01NfDZDKhb/9+6J7SXcDxKNFfAhLL8WS/pKRukMtkyM3NwfXs62jXvt1Ln1csErOPc3NJhVJZcebMmTnOomTookWLJn/22Wds8+bNqV27dmV16tTpnms0/x+V4yacyWl1o06nMZtNnEQiceqxF3HXs7PpkpISIi8vTxQdHQOr1QKapoVxdh57ycPFCxewaPFipPRIRXVVtVCFNQXl7HY70han4cH9+4iJjcUbEyfi4cOHYFkWdbW1aBYWCtrB6yboGxtRW1uHhA4d0KBrQGqPHujWnRfUb6irBymiEBAUANpBC0Q9iVSCF7X8WrvYuDg06hpBUiQkUikYp8pf0zDuykl+65X+mqG58ko3dzfM++B9bNm8Bb179ITRuSunsrKCx8osFlBOTXmXbtaBfQdw/vw5uGncwLIscnNzUFxUjNMnT0EikeDOnTtYtWY1hgx9BQ67HSYTj7xfuXwZSxYuRnlZOdZ+tw4ymQwMywj3tq6uDlkZmbienY2AgAAEBAZiy+bNkCvkeH38OGG9itVqJXv06sns/nmX/7Rp0w78+OOPwwmCsABYS1EUCgoK0KlTJ9duSvofVk1OS0sTpaamMtOmTzNfvHhx6KNHD7nw8HCmsKiIXbpoCWUymiilUknWVFezr44dQ4jEIkgkEjAMC4NeD6lUipycHDx+lIt3Z0x/iWrTlD6r1Wqxdw/PXujYuRPWf79BGI06sH8/5HI5krp1g9lshkqlwoP79/Hjjp2IiY1GzqMcXDh/Hi2jouDv7w+7w8FryzsNxWW8CrkC1VVV2LB+PfwDAhAYFAiapvGsuBgSZw/RhRu5Kj1XUuv689ulTb81Ntdn8vDwQKfOnZwArRaNjY24ef0GEhLaQyaTQW8wwG63w9PTE9u2bMXK5ctR8qwE+U+eoCA/H7oGHUaOHgVvbx9I5TLMfX8eUnv1RH1dHU+8I/hRtXYJ7RETE4OtmzdDb9CjR4+eYBkGDsaBxsZGmIxG+AcEIDExCUqVSlhrd+zIUQwfOUJQX3Q4HAgPDyc5juO2bd0W065du8RFi9Iqjh07WjxixAiJt7c3MXHiRGRmZrL/FDnuzMxMNi0tjZw3b979hoYGn9s3b7XLyswSX7+WTXl6ejYuXrx4Wfv27QsPHjiYYHfYuYQOHQiGYWDQ69Gob0Te4zz8uns3klNTkNIjVaiGmiove3l54Ub2dSz4cL7gzvOf5MPLyxPR0dE4dfIk7t65i8GvDBG2L1zKzEL2tWzcu3sPOY8eobKiCsePHoVMLkdCQgIf6siXQ5tEIoHZZMZPP/6Iy5cuw2g04Mqly9i7Zw+e5D1Bx86dIJVIX5Kp/KM/f5RXuUJ202XhFEUhIjKSX5yQkIArl6+gsqKSH0K1OWCz2/D82XMcP3YMz0tKhNcMDArEqjVrMOmtN9E9JRl9+vaBp6cXLBazAFG4frfRaERUTBTu3b2L69nX0X/QQD4EMiysNiskUincNG7QarUIDQ1FXKs4nDx+nHuc+xjNm7cgYuNiha0WNpsNHTp2IAKDguhbN282v3Qp89UVK1YcX7lyZXnHjh2J9evXs//UzRTp6elseno6IRKJ3i0pKdlcVFTUQ6fTcYMGDfqRIIgaAHj33XdN27dsm3El6zLBAdTjx7mwWqzCawwfMRLEb5RfSJLEwwcPcerECWRkZGDAwIFI6ZGKmzdu4vjRozh8+BB69uyFsrIydO7SBXq9HuBcT1cEBgwcgJjYWHTq3BlSqRS3b93CJ0vTodW6o1///ryQmegvync2qw0///yz4MEyLmZAq9WCYVgUFhZi6+YteGvyZIHP9f9K3lmWhUwmw4sXL3Ap6xL6D+gvDKi6cjOj0Si0Y958602wLAetVssXPwYDmoU1w+pv1uD8ufO4cvkytO5avDr2VQSHhKCutlbgktXX10MmlUGlVgmLn1x8MRcbtaKiEgRJoEHHT2R7eXq9JFmpUqu5H3fs4LIys0iNRoO9e/aw/Qf2J1zpDknyG2o7deok6tChg23aO+9Id+zYsYzjuMFLly7l/juXjf9OdXfq1KniTZs20TKZjGvfvv3TK1euhJMkyXXo2JEMDglG6fNSXM/OxqQ338T7Cz6ArkHH97Cc1dPo4SMhlUoxbcZ09OvfX6iaKIrCgX378dUXX4LjOHy5ahXi27aB1cl11+v1KCl5ho4dedEzXs3GG0sXL4HJZMInny2DwWCAuzvPKNBoNDh7+gzmzp4jGFZiUhJ8fX1w9epVVFVWAQAiIyMxc9Z7v9MU/UM+lkyGmpoabN2yBXmP85DQoQNmvjfzpbW/vy0IRCIR/AMCYLPZ4B/gL/QPXYsJXLnmbz17Q0MDrBYr3LXu8Pb2Fka/eDU/Bf+5AHy8ZKEgJuzh4QGJVMLv5mFYbsVny3H+3DmiTZs26ZMmTSr6aMGCHYvSlzh69+4jdumdmkwmNDY0wj/An/1i5eeEvrGx8fz5814EQTD/nbt0uLS0NNKl5DZ16lR66dKlDMdxkkmTJm3Yv39/2KtjxrD9Bw6g/Pz9nG6bwpKFi3D79m1BUbgpiBgaGor4tm3Rf+BAWK0WgSpDEATenPwWOnTsgNLSMkRERMBm5ecHVWoVThw/DqVSBYZlBQEMi9mCsPAIGA16/kllOegadIKwv6+/HxI6JODWzVuYPnMGho8YAYbhx/MXfvQRCp8W4unTp6iurkaLFi2EpP+PjEokEqGiogJrVq1G18SuePvddzFv9hws+3QZXnv9NQQGBgpSQE0LApZl+baYv7+wFIokSRj0BuFxb8pbd3kmjVoDN40bauvqcOLYcUikEvTr3x8qlQo7f9iBC+fPYdXq1aAoip/flCs4m83mGtxg5r//gaiivNyxcOHCdQsWLFiakZEhOXnixPQVny7v6OPtY2vTtq3YZrMRZrOZkCvkkEgkXF1dHTiWrfsfWdLkJHmxaWlp5OrVq2UpKSmOjRs3jjp79uyk8W9MoN9+9x1RSUkJrFYraJqGVquF1kMLi8X8kp9kWRZu7m7o3LWLc7WuCFbry83UhoYG+Pj6Qqv9i3qKm7sblEolErslob62Tjhk1yHU19UhKibqdyotjY2NCA4OxoBBA1FeVo6BgwbB5hQp8ff3x1tTpuCLlSvRq1cvhIeH/025SRcXa+eOHbDb7Zj7/vvw8fGBv58fFsxfgPS0pfDz88Obb72F5i2av8TtcjWUxc4HSNhCRpF/LGvpJN8dPnAIeU+e4MH9e9A36uHm7oZbN2/xy6oOHwE4IDs7m/P28eFIkmSOZB0Wnz1zFgzDwG6ziWRSaeX8+Qv6z5079363bt1EBEHQHMf1HTBgwOm5s+Z0bNuuHaJiohAZ2Zx2d3fnTp08RRQ+fUr16NFjFUEQTHJyssgpgPvfuv2LcBqYxflvU1h4OPv6uHGsvlEvlOgSiQSNjY24ffMWBg4eBIqkXjqYhvoGdOjYARGRkcIu59+ufLNarbDb+ENWKPkNoxaLBS1atgRacCh9XupUYBbheWkp2rVvh/g2bQRdKYIgYLXxOwVtNjuUShVUzuUGNpsNJEFAr9ejbdu2WLxkiTPnYn43ccw5lWWaQgudOnXGzh07sOyTTzFw4ABQYjEv9wRAIpWipKQEoWGhQsLNsiw0bm4ICQ2FxWKGTqeDr58fHPyewd9BGzwz14aZ02agvr4OYeHh6NOvL8aMfQ0EATx79gwN9Q24ffMWCgsLseeXX4k9v/xK+Pv7k1ar1ZGYmGhs2aIFdI2NR+fMmfN5XFxcLgAqMzOTdq410XEc13/69OnTbt682a+osLCNyWRSOqUuue5JST/8+OOPWyIiIv4mxPDPMCzCaTDc7du3uxYVFfUnCILed+BAm6OHD5OlpaWiFi1a8IK1Tu0rXYMOOp0OrVq1RnVVDQgSwrLHmzduQuEUdnV1310eSCqTwma1vRQa5HK54IlcuVbh06eQSCUIDg5ByxbNodZoIJVIYbPbUN/QwDeCpVJYrBYwNO3UDdXh4YMH6J6SLGjQP3jwQAB0XR7GpVNvt9shlcsFrpaLFtSrdy/U1tbi2NGjOHf2DFiWQ0BAAL79bh1atmwJnU6HmupqtO+Q8BfOlNXmpNBIce3KVZjMJkRHxyAiMgIqleolop1ILMbhAwdx984djH51NN6e9i5UKhVyHuXgUlYWRGIRCgue4tmzZ9BqtY7JkydbzGZzBQnsHjh48OG+ffsWAiBlMpl+69ataIqWEwTBOgck6gEs8/T0XPb8+fPA06dPT5RKpSRFUeeHDBlylfg72w//peQ9LS2NXLp0Kfnhhx9uOnz48CSXrGBNTQ1MJhPi4uLwxVdfwcvbCzUveC1Lo8GIcWNfw6w5czBk6BBBc5SiKNTV8aHM09NTUKaRy+Worq7G49xctGvXDloPD5SVlvEbUF0Lw5sAmLdv3kaHTh0glUoFmcMH9+7jwvkLKK8oh8VsQd/+/dCjZw8YjUZoNBrs27sXu376Ga+88gp8fH1RVFSEi+cvQOPmhilTpiA0LFQIhUcOHUZOTg66pyQjMTFRMC5X7mO325GethTV1dUgCALLV65A95QU1NfV8SNtbhrI5fKXCgHXsC1Jkji4/4DLMNA+IQEOux0GoxFuGg2CQ0JQXlYGk8mM/CdPcP/BfeeWs4ymSz0ZANQbb7xx44cffugFgHYCmy+xWdLS0vBHXHWO44i3335btGnTJsefKdb+6Wvl0tLSRJ988gnj4+Mzed26dYtjW8XRc9+fx3RPSWbrG+pRVFhI1tTU4NrVK2gRFYWw8HCUlJRg66YtyH/yBMkpKUjokCAMKLhKcIVcAYIkhMpNrzdg1oyZ3E87fySuXr4CX19f+Pj4wGgyQq1Rv9R6MZtMqKioQEhICH9gVgvych/D7rDDaDTiyCG+N3kpMwsKpQKtW7WCVCJFmzZt4e7ujseP81BcVAyz2YyRo0bi7u07OHf2LKRSCQiCxIH9+3Hy5EnU1tbi9q3b8PL0RERkhECNcXUWNBoNnj59isCgIIyfMAF2Z5Na66EVtNqbPvj6Rj1MRhOkEn60LS6uFSiRCGWlpbDZ7bDbbLh18xaCgoMRGhYGbx9vdOzUCUVFRTh04CC6de+OGTNnoKa6GtXV1RxBEGRQUFDJ66+/viE9PZ2ZOnWqeNCgQcjIyMDSpUuJ9PR0LjMzk/srOTNu377NAiA4jiMCAgLEgwcPptq3b4+/9jP/dI/l7u6OV4a88uTSlcuRO3/6kTOZTJTrqX17ylSUlZbynCmFHCmpqbhz+w5ohwNvTn4Lw4YPF7bHNx0Qzc3JhUQqgaenJ/Kf5GPzxk24e+cOPDw8UO9cNjBi1Eg4HA68MXEifP184bDzq1FcOvItWrYA7XDg0cNHCGnWDP4B/pDL5biefR3z5sxBdVU1WrVuha3bt4OmabyofSHgQZs38L/v+fPnwvbTv/X5P/1sGb/k0+k5XZ+jvr4eNpsNca1agRJRYBkWHp6eEImol9B8ANA16Ph1xnJ+26uLliKTy8ByHDzctSgvLxe6Eq4K+uLFC/h8+Up8t2E9mrdogSd5eZg3dx5jMhoptVp948iRI4lLly7Fn0my8e+0ulckEgEEPLy9vQgXVgOOg1yhwKzZs/DD9h/wODcXFrMFJ4+fQIeOHbHqm9Xw8PDgRciaqNdJpFJUVVXhw3nvo7q62sUJYgGQoaGhNRs2bJgxY8aMX+vqajFoyGDCbDLj5s2bSEpKAsdxMFvMqKmqRlhEOMRiMV7U1MDH1xc+vj4wGAxobGxEQocEzJ47Fx/PX4AePXtCpVKhtKxUoPMcOXQE4eFheG38ODy8fx/ffvMNal/Uws/fHz169ECr1q0ERee9v+6Bl7e3kOf9VgTNJeZvMBjg4+MDSk6h9sUL+AX4C7sVwXGwORvvrurQJRFls9tw48YN+Pn5wWa1wl2rRWBQIM/4tPO6XLSDX3Wn0+lgcQ4D+/n5UYVPn9LBwcHtamtrkzIzMy8lJyfLMjMzmfbt22PQoEHM3xrX+pcbVlpaGvnFF1+wcrn88tOCp0OfP3/OeHh4kK4WTOv4eHy1ZhUe5z7GhfPn4e3tjbemTBYotS+xLjlAKpXwLY7KSgSHBKNd+/YoKy3jcnNybN26dUuvqKhQGQwGYu777zMR4RGUi+KxcvkKlJWV4kXNC/j7++OHH3eCoRk4HPRL1GNeU9SEFi1a8CtbvL0FGEOlVuPC2fOIiIjAkKGvwGQyITo6ClHRUfh06SeYNmMGevbqCauNn35pl9Aez58/R7t27fi2UJMKtmnzmZcXZ52j9QqQbgRuZl//ixdVKGCpquYfMJIQIBSVSoUftm/HD9u2w8PTA/Pefx9t2rV1PchO8TMSQ4cNRWZGBtZ++y2++Oorp+dkXW0wkVwud1MoFExWVhZDEARu376N27dv449Wk+DfZXVvRkYGsWjRIu7ixYs5O3bsmFJZWUkOGjKYYBiGEOgvHBAQEIDklGSk9kgFy7KCMIhwCCQBi8kCfaMeYrEYF89fQFBgEKxWG3fv7l2iefPm1WfPnp1z5MiRFY9yckLenT6dM5tMJMuyiGweCa3WHfv27OU3ZtXXo3nz5ohr1QomkwmVVZUICAgQtoS5u7tj9apVqKysxJw5c12LuHHm9BkUFxVhzOtjBdTeZDIhKDiYX7Tp6QmxRAKL2Qy73YG6+jo8eZyHNm3a/E4qoKlxSSQSyJ3UZZPJBIVCiYaGBhzYfwA3b9zA1StXoFGrofX4y+4dsViMn37ciR+2/QCJRAKRSITp782Ah4cHX0A4/2MZnmXbu29fHDpwENezs5HaIxW5ubkoeVZCNjQ0sNXV1QP9/PxCy8vLY1mWTUxKSkq6cOFCzYgRI+r27NlDuTbl/nde5N+dlBEEm5aWRmq12kedO3fed+PGdcpgMDCuJNYFFbiqKYPB8NLXXbmVUW+E2WKG1WpFREQERo4ehbt37yL72jWC5Tji+fPngaHNmhX++OOP7YwGAxp1OspF6mdZFr379MGSpUsFD3jp0iVYrBZ4e3tDIVfgyuUrMJvMsNvsWPXFVzh25Bi++PJLBAQGQKVS4fsNG7B96zYMGzHsJcFY1zS33fYXjjhFiYStDyq1GtnXrkGtVv9lSptlhV4eTdOorKqCh4dWgClMZjOaN2+OWbNn4fVx46BWq5G2eAkaGhoEMqRILEbp8zLI5XIEh4TAzd0dGo3mdwAtj8PZoFapMHvuHDx88BAVFRVI6tbNhZORly5f1mRlZb1N0/TK4ODgz589e7Zy4MCB5xctWtR89OjRjHPzyL+XYbl+jqZp8tVXXz3CsRx77MhR1s/fD1LnQZAkCa2HViilXXmEawScdtACV8u14q13nz54+913sPSTT7B1+zZs3LKZS+6RqigsLFTU1dXhp507nZPTPL1Dp9OhR68eCA0LBQCER4TDaDCivqEekZGRqKyowNBBQzB08BB8v2EDopzaEOXl5dj4/fc4ffIUvln7DVq0bPk7RNxut6O0tBRyhQIMywjUFIZhkJKaiitXruLQgYOC1pdcqYSfnx98fH0RGh4OmqZx6dJlMCyDnJxHuHfnDtzd3aF0ft+Y116DQqkQli24QNDW8fGgaRoWixkV5eV4/vw5z6tyJu5N17dYrVZEx8TA3d0dt2/dRtt2bfH+/A+xbPln2LR1M/ftd+vopO7dHEOHD6PXfPO1nQOC9+/ff+7o0aOB6enp+O82LtF/sZ1DA8CgQYOOdujQofq7tev8VSqV3dfXlwwOCSH8A/wps9n8EmLt5u4OXUMDu+ijhWRFZQXem/UewsMjBL1yPz8/zJ47B1arFQ0NDbDb7MRbkydzD+7fJ+7dvccrB1IU7E0E8Q0GgyA/1NDQAIIk0ahrBMuyCAsPF0RqASA3JwfT350GkVgMd3c3bNi8Cc2bR0Kv1/9mywQfbsrKSkHTNNzl7uBYDidPnMDOHTvQUN8Aq92G+/fuQ+uhhdnMLzKQSqU8/EAQaNu2Ld6fOw8njh1Hm7ZtcO3qVeTk5GDIkFcQ1yoOFeUVwrZYobXFMAgMDADDMKgo57XYsy5mokWLFlCpVRBRImHIxCW9JJXwVKOSZ88gEonQtm0bULzgGuHl5SV6bdzruHfnHry8vfHxooWO9+fMCTlx4sQCkUg0Mzc3l/q3M6wmCnCmPXv2jGNZdu+Xn3/hoVQqIZfLsShtMdstuTupa9Dx8kImE3PtylWs/eZbymoxcxwHZsGH80XLV6xAWHg4j2UpFQJHW6lU8rt3GIbw8PAEQRCIiY2FxFlVkc7pZU9PT7Rt1xbl5eU4fvQ4klNSENsqDnabDSzLoFOnTigrL0ePHj2Q0iMVKpWSZxP4B8DT2xMGg+Elo2JZFkqVEgX5BSgrq4BYLEbe4zwcPXoUP+3YCbFYjLhWccjNfYy5789Ds7BQHDtyFPX19YJ2vQs+ePvdd/D16tU4eaISRqMBjx4+wsH9BzFoyCDIpDJ+y5fDATgRfLvdDv+AAGi1WlAiEea+Pw8BAf64fes2KIpEXW0dgkNCEBUdxXc0rPyol81uR3V1DawWK+x2G8QcB9K5m1omlYF1cuICAwIouVxBK5XKPlKpFP8vqcf/8eS9CfGPcy5PLC4oKNgSHh7uSEhIuHfr5s36E8dPtBBRIi6kWTPi6OEjWPXlKvLYkSOkv59f4YoVKxNnzJhxfd/efSNu3LhB9+vfj5RKpRBLxC+zPBUK6Bp0+HHnDjQ2NkKr1aL/wAFw0I6/SC8SBLp07Yrsq9dQWlqK27dvo662FhcvXIBMJsO8Dz9A9+7d0alzZx6xl8r4DRTOMf/fbgQTiUSw2+xYvuwzNGvWDCCA+/fvwcfHF1qtFuVlZbDbeNA1pUcKwsPDoVDwD5NrJ6GrMgwICMCgwYPQUN+AWzdvAQD8/Pxw5fIViCVi9B8wAOHh4VA6VQh5qSV3dOveDak9eiA2NhYymRwqtRqPHj7Cmq9W4cD+AxBTIgQGBYLlOPyyaxebmZFB1NTUICQkBM1btIDNzvc9RSIx9I2NMFss6NylK06eOO64eeOmODIycva1a9ceJCcni0pKSv7bjIv4R1/gt1MaGo0Gr7/++q6TJ0+O1uv1jEatIdu0bbNn1qxZ2SkpKTsIgtCfO3eu/zvvvHPCZrfRGzZtEknEYri5uwlgI8MwPAi5NB2/7P4FAQEBfEU3by7GTRj/l8lmhvcw9+/ew8wZM8EyDPoNGICwsFC0at0akZGRMBqNv1tOSVEUPDw9/vDz3Lp5C1mZmYiOjoa7Vovo6Gh+g71cjt27dmHtN9+CJEnExMbigwUfolHXCH9/fz53bCLyxrIsxGIJCAIYOXwEOnXqiGEjRmDzxo1YtGQJVCoVv0Gs6dQ4B6e8JoH6+nrntjJ+iqi+vh5FTwvx808/obq6Wthe4XA4OIvFQowZOxbvTHuXB5MJQCaToby0DOfOnoOHpwezb+9eqmWLltuzsrLebqI1in9bw3L1mZYuXUo5CfYOhULB/frrr4GDBw/m9uzZQ7z22mvlzp4WkZaWRqxevbo/zTBH574/l0lMTBJxHAc3dzdBz1ylVuH0ydP46vMvYDAYEN+mDfLzn4B20Dh87ChkcpnAPBCJRHDYHfyCgegoNAsNA+vUYFCr1XDQDpiMppcOXCqVQuOuEbpfLsZkZXklv+pO6+4UyeX42T6xGCIRBZvdjvGvvY7aF7UCAi8WS9Czd0/MeO892KxWYbN80wmft6dMRdeuXdG6TTxu37qFGTNnora2VuCZN50ScnNzg1jCFz0sx68/sZgtsDlskIilYFkG675dxxw/epT64Ycflhw4cODKwYMHz499/XXm3WnvUlaLlR8MkUhQWVmBiePfYCwWC9m+ffsN9+7dm84wDPEXFPHfMBT+ts+UmZnJZmZmMgAIh8OB3bt3GwiCMOzdu9fAsiyVlpZGGY1Gavfu3Uxqamqr6urqV5O6dWO8fHwojmX5VXXOQ76efR3Piosxf8FHGDhoILKyMpH/JB9J3bph0JDBQglOUiSsFivmf/AhXtS8wKDBg1FfXw+HwyEwO2UyGRx2x0vsCLVG/RJQa7PZYDKaIJfLBQkgmqYFDS+FUgGRWAyNRoOYmBgYjEaUlZY5talMePTwEViGRc/ePWEwGl5SIhSJRLhw/jxycnLQqNNBIhajXfv2YFlW2Njq4siDAxRKxUujZhTFC9lazBaYTEZotTyn7VLWJcJsMFjyCwp6OGhH2HvvvQe1Wk2wLAPCCe14enrC3d2dvXH9OuXv73+gqqrqcrdu3f5bQ+A/1bD+yBOmpaWRGRkZRFpaGuE0OraiogLp6em4cuWKKDMz87VjR48qEjoksEqVStjeqmvQgQCBpG7doFTzS8T79O2L7KvZSO2ZivYJCTCZTOA4DiqlCteuXsWmjRtRV1+P3n16CyuACRCQyPiJG7FILCgvS2VSfjO8zSFAIAaDASzNggMn9Pxkcp5X3vSQGYZBaGgoBg0ZjNatW+Pq1auwWmyQSiW4feuWoAHv4oCB4w0jJKQZgoODcf/+Pbi5u6NL166oqalBUVGRsCVMKpWCoAjBWzW97DY76urq+JUuNS/w5edfEvV1dSgtK2vOMEzYnHlzEdeqFWGz2fiF5s59hQzDoHPnzqRILKKzr13rM2XKlGu7d+8u+O/Or/5pofDvrSbT09PZ/fv3d160aNFRk8mk3fHTTlIilRIkSQq6CC69dtfevZ9+/BHHjh7F95s3Qa1W8x6FEmHaO+/i8qVL4DgOffv1w7vTp0GtVsNiscDNzQ00TTsV7xRY9eWXiI2LQ5++fWEymXi1GpUSSpUSDrsDdoddGE51EfL+aHCCZVn4+Ppi7+5fsGTxEkH9TkRROHDkMPz9/fkBDkoESkQ5N9VbUFtXC7PJDC8vL3y/fj0OHjgITy8veHt7o0WL5pj6zjsIaRYCo8koiO+SJImKigpcz76OsLAwLPvkEzTqGjH9vRnw9fNjRSIRPDw8SKVCCYlYDBAEKJKESOwshgCIJRJ29IhRGD161J3169d3sFgsf0qr/V8BkP4jYZO9ePGiaMSIEdmffPLJNKvFQp06dYpx17oLPCqbzSa0Y0iKBM3QEInEeHD/Aaa+NQXXs6+jqLAIc2bNwqWsLMjlcrRLaI/Tp07hzTcm4tChQ/D24Sef7c51IgzDoGVUNKKiowTFQZLipRZpBy14N9dChL/Gc3cN2DY01COhY0dhXW77Dglo3qIF6urqIJPzr+OSwbTZbPyyBUoErVYrNKnFYjHq6+uRm5ODQwcPYcmixXic+xg2iw36Rj2v0wUC+U/yoVKr8Jhv22DK21MR36YNNGo1qVIqSbPJDJPJBIZleYE1ZyikaRoSqRQms4l12O2k3W4vZBgGo0aNIv4t2Q3/6NWjRw86OTlZNHLkyCPjx4+/26hrjKdIimEYhnIltH9QIoAkSeTm5GDypDdBUZQgABfZvDnmL1iAJYsW4UneEzy4dw/yqVP4sSwPGWw2G+x2OyKbR8LNuYO6aYLtoHluWH1dPeQKOVRq1V/lubvyNA+tB04cPQ7/gAC8N2cW2rVrh7LSMhQ8yUdoaCi8fX1gtVjAsAxsFttLkk4EQWDchAkYNXo0VGo1Htx/gE3ff49bN29i9IiRiI9vgzGvj0Xr+Na4fOkSTp04haRuSTh48CAAfoOH0WiE3WaDWMxPo5vMRtAMv+aOIin4+vpCJpeDpWl2+SfLRHKF3BQdHZ1mt9uJf1vazD+hikRmZiZLkiTdr29f7vjRY+T4NybQarVaWBTQVG+K9y58eNq8bSvszpEokiQxfdo0mM0mfLd2HUqfl4ISidC3f3/AScsBAIVCAavVimNHjmL8xDcEja2mxmMymQCCZ3Vy4AXUXKHot2FQKpVi6+YtWLl8BVZ8sRJdu3ZFXW0dQkNDcfnSJUx7510MGz4MHTp2hI+PtzDPR1EUrzklouDj48OTBFkWQ4cNRe2LGuzetRsfzP8QzZqFIjSsGex2B/b8sgcPHzzAlcuXERoaigUff4z6+jo4HA5+Oolj4LDZIXV6W6lUCqPegIwLFzm9Xk/v27dPbLNYTAMGDhw4bdq0J85UhPk/aVjOXAsAyMTExLlz58498uYbEzVfrVlNh4WHifSNeqEicnNzA8Mw2LdnL9q2a4e2bdvCarVCJpPh/v37YBkWTwueOlXntKh98QIxMdEv0WZohobVYsX4NybATaN5aQuEVCrl5+iMJsHQrBYrVCoVlCoVLM6Wk4tCrW804HFuDnbv2oV33n0Xvfv0QV1tHa/byTIQicR4nJuLsrJSrPj8c/j6+QoDIBzLQSwRgyIp6HQ6IY8zGAyIjomBXCFHl65d0aJlS17/XiLGq2NexcMHDzB02DBMnjoFSoUC6UvT8bSggO3ZqzdptpoR4BeA4KBg6A0G5llRMXnjxg38uvsXgqZpcY8ePRrHjh07dMqUKZnJycmiPzsM8e9aFf4p5D4lJYWYPHnys/Xr1196cP/B8O83bFD4+/mjdevWkEilnNlsZu/dvUd+krYUz5+XYvXXayBzDlfYbDa4aTRoGRWN3n37YMrbU9G9e3fs27sXMpkc3ZO7w2KxgBLxEoku+rCLxemw26H10EKp4j2Ta1rbxaH/cedO5OXmISo6StDmVKvV8NC6w9+Jqnfpyu/LcVV1IpEI0dHRTnEyB4YMfUUATq9dvQaKpNAstBlfKDiFQAQNC4pC9tVs7P31V+Q/yYdGo4afnx/8/Hyxb+8+9OnbBwkdOuBSVha2btnCFRcXk5cvXWI6derEtmrVit2/bz+37tu11JHDhwmD3kC0atVK17Nnz7X79++f0L59+4ejRo2iTpw4wfxPnS+Bf/HlQu4NBoNPQkLCgrKy8vcSOrSHSq2m7t29h/KyMrZZaCi5+us1CA4O5o2lCQTg0vRsbGxEQEAAdu7Yge/WrsOmrVvQsVNHYStZU8NxkRJ9fH0ElT6dTsdLf8tk2LplC37ZtRshzm2vrs31YokYWq0HFHI5v2KX4EHSplx2kiKhkCtx5PBh/Lr7F7SObwWLxYrjR4+B44DPv/wCqb1S0VDXwL+mWMyvwqMZWCxmVFVV42lBAW7fvo24uDg0Cw3Fe9Nn4MMF8zF0+HBs27IFe3/dg06dOuVfvXq1hZubG5QqFcpKSxETE3MpKipq5ZQpU4q6du1qJAiirGkl/j95ruS/2rD27NnDOtmT1ry8vOszZkx/brVYyboXtcW6hobTbm5uZGJiV7p169aMS/bbRSMBALPZzOu5SyWoqKzA0GHD0LJlS3z79deQiCVC66epEgxFUaivqxMkuu3OeT6XccTGxvHUH08PaNw1PJQgEsFsMuPunTt49OgRCJJvHNMOGmQTkRCGZmA0GpCSkoK+/fri+NHj2LdnLywWC9RqFW7fuY2GugZejtFNA6VKCYqiIJFKoPXwQOt4fr/24rQlePz4MWa8Ow2hoaFo1z4BHMtyz0ue08FBwcbjx48nLVmyZK5er1+fm5Pz3ahRoz7Kzs7u/sMPP5xITEzMIwiiLDk5WfSvMKp/aSh0GhXVunVr9vvvv588e/bsA6tXr56YmZnp5u/vTy5atGjV3r173x4zZkyz06dOt7+enU1WV1fDTaNBQGAAZFKZczkBLST5dge/NCCkWTP8uHMnSIJEt+7dwDAsOI6XRZTL5Thx7Dh2/rADFEmisKgIDx8+RHhYuJBLRUdHw2Qy4fy584iNjYWvnx/0ej1PUDQYsOG79WA5FrFxcWBZFlWV1VAqlcImNBchL6FDB4x6dTRYlkV5WRmWf74C0dFRqKioQGBgEAiSeElji3XKBBiNPMJeWVmFS5lZmDVnDjp27IBTJ0+y+/fvF7VpE7/Mw8OjYdy4cSar1fro22+/ffLGG29UzJo1q8O3335bk56ebt6zZw/11VdfMf+VCZv/1aFwz5491OjRo9msrKyOM2fOzAYBjH/jDVoqkVC//vIL+7TgKff6xIlJ365adf3TTz/9YsWKFTGNjY39VSoV0T4hgQgI8EfvPn2cdBoJLGYL9Hoe+1GpVTh14iTWrFqNnr16IiAwEIUFT4VPe/XKVQBASo9UDBw0EIGBQQgOCRYYpC427Pmz5/i2kFyGiMhIeHt7QyyRoLKiAh/MfR+pPVPh6emFS5lZ+OSzT3+n+sevy+XxseNHj0OtUeFZ8TNoNBr07d/vrwrrMjQNrYcH1n6zFt+vX4+1679D4dOnzJZNm8no6Ojls2bNurtixYp9RqMREokEDQ0NcHNzc00NVQwaNCjtyy+/3LJ48eJ/ibf6V+dYpEgkYufMmXPkp59/GrR9xw5aLpeLnRgTM3nSm1S7Nm0OHDh0aATLsrh9+/aQESNGHNbpdEzzli2oyvIK1NXVwd3dHUFBQfD08kKf/n3Rrl17WG1WuGk0SFu0BGdOnxaATZZl0a17N9jtdnTr3h2vjx8HsVgsyFX+diGUK/F2hV7X3xqNBrmPcjD5rckw6PUY8/pYzF+w4PfbLDiAZmhBFWfBBx+iZ69eL43A/R6t4yCTylBTXYM335iIhoYGLFy8CNu2buPsNhuWLFmy5uOPP54b37YNt2jJYlokEhE5Dx+htq4WIpGYO7Bvn7iqsgoTJ07skp6env3XNEL/z8INTQ473N/fH2q1mqyqqhK2e/n4+XEERUUwDEMUFRX5TJs2bRXLcdyW7duIgMAAGAwGFBcWIzMjA/n5T5CVlYkL589jyNBX0LxFCxgMBkQ2j4RMJkOLFi1QVlaKhw8fYuJbbyIwMBBBQUECpaYpD6xpgu9SOm4KjlIUhcbGRrRuE4+uXbvAarVhzpy5/ABuk5DmAlIVMgXEYl7o7aOFC4VB178mjeRC2gsKCqBQKFBeXg6xRIJBgwYR33z9NWbOmDE3rnUrrFqzGg6HQ8wwDLokJYK2O9Co16N9+/aON8aNFz24d2+hSCQa/D8xOPHvZliEc8z+bllpaWxVZSUTEBhIORdjMmXPn1PBgYH3CYLgHA5HXG1tbWTvPr0Z/wB/qrqyGgqlAi1atkBUNK8oU1CQj03fb0Lp8+dQq9VgWRaBgYHo0LEjEhISMOPdaVAoFAgKDIKHlwcaGxt/R/YTjAKEMJX9W2CXV8dxR0F+AUqelWD23DlQqpVo1DUKjV+FgsesjEYjv13j4CFUV1Vj+ecr/lAvq+nA67Wr12CzWtG2bRtEf/kFPnz/AyxdvAQ0TcPLywudOndmZs2dTTocdsJm46WPTEYj7FY76l68gJ+/PxkQGACCJMP/1p7F/7OGxTmVKGbOnPlZZmbmyLlz5speGTaUEVEkzp09J1GpVOZRo0Yt37t3LyUSieopimJcizVdYaSpkkx4eATen/8BwkLDnEspj0Kv1yMwMBB2hx21dbXQNejg5u4GhmZeoiQ39UhqjQYMTb/Eq2p68CKRCDkPH+Hg/v0YMHgg8vPzER0bA7WahyS0Wi1uXL/uNPJS1NfXCe9z8CuD0aNnT+h0OiEfayo9abfbERgUCJlUBppm4OnpidGvvopv1qzB8BEj8NbUyfD19aV42SX6pc8gk8vgFxCAhoZ6pqSkhAoKCLrnTCv+JenOvxTHckrosCdOnOizcePGZTXV1R1YvjK7Pnr06IWzZ88+77zhKbGxsZuNRmP4mm+/QWhYKGk2m6Fv1AuLtTnwTdetm7bg9KlT8PPzw/Pnz+EfEIC1363Dnl9/wZHDR5GRlfnSijYXJflFTQ0KCgrwOOcx2rRrg/YJCUJIo2kaD+8/wJMn+Wior4fNbkP/AQMQHRuDDevWo6ioEIuXLIZKrcbpU6fw+fKV8A8MwNP8AnAchwGDBsLL0wv37t3Fpq1bBB6WSCTiN3KwLC8Op9MJbSOeXCiCrlEHm8WKuNatXhqmaEoOlEgkyMnJ4e7dvcscO3JMRHCwzZ4zu9277777OC0tjfhXJPD/coC0yQZ1AkB755dvO1fEun/wwQcbjx07NqygoEDMMAzn6+tL9O7bB/369UNwSAhsNh6F17hrcPTQEXy/fgNWfPE5OnXpjMrycrw/dx6USiXmzJuHKW++hXenT8fMOe+hpqpaIOK51gzfvHETJ44dx7jx4xATGwuRWASO5f6/9q48Kooz396vqne6abqRTTYFVEYBF0RARURN1MS4RRiNewyoiSZx4hgnGpU4MxonJioxUSIaFULEDZeMiZgIirjgGhEBg+IGgkKzddNb1ff+qO4OZpL3Zt6bOaKP3zmeA+d4DnWqbn31ffd3f/cKgeYMg9LrpSAMQUiIwHOZTWbU1tUh/+QJWK1WHMvJwaWLl+Dt4wONxgXXi6/Dz98Pm7/4AgGBgUjfsQM1NTWIiR0Eq8WChzUPERIWCplUhubmZse+y0Xj4lBZtJ51/KWprj0J7KcbP9E5iUlEq9XC29v7wrhx495fsGDBkSfFYbUJYP0GM8wC4BYuXLhjS9qWqXFDhvCDh8QxdY9q8emGFNTW1sLV1RUjX3wBgwbHwsfHBzU1Nfjb6g/xx3ffRfSAaNQ+fASVWo0HlVUY+9JoLF2+DOfOnsWB/Qew5P0lGD/hZYAA+mY96mrrhGns48dRef8+XktMdGzc7ca1EokEBqMBKpUKLGFBGABUaMU4OSnQ1NiEP3+wEiUlJVj14Wrs3b0HWbt2ISYmBv2iIsGyLIYMHQqe41F2owwMYVBUdBUKJyc8/9zzIAzBo0ePIJGIERAY+Jgbz681w+3T3DKZjJ8Yn8CwDGvct2/fzE6dOu0mhHBPElRPnCBt3TeklJIePXqw7777rig1NZWjlPZZvHjxR127dsWK5GRWqVSSkNBQiCVinDt7Fnq9Hj9e+RHFRdcwIGYgysrKcKbgNF59bRasnDDmbzAY4OHpgdpHtfjm8DewWi24e/cuTuTlCU7JLhpota6OT17nzp3h5yvwWfYhB4lEgvqGeujqdIKHaUOTkFnt+BxRG3emgp+fH07ln8SMmTPxqLYWebm58PD0xIgXRkKj1SDveB78O3dCVHQ0NFoNugZ3g5NCAZlC5tDHe3l5PbYytf65FQ1CzWYzX/uoll+xbDnz042fzDNnzhw7ZsyYA8nJyeRJff7aDN3wi40zBcBlZWVh+fLlBICMYRl5127BnF6vJ/YNcLdugtmst7c3WlpaEBAYCHd3d8He59gPKCoqQkzsIOht8hu9wYCJr0zEd99+i9KSEgdl0NjQgIz0DIT17PnYKiB3UuDmzXJ4+/hCKpGApzzSd+xEbW0tunbrhp5hYfD1831seloIAW+Bu7s7zGYzfvj+e8GLwscHH6//BGoXNUCBoKAuyN6fjYaGBnh4esBsFnxPLWaL0HfUuMBisUCv1wuiQ/HPosNW+y764V9Xk3PnzrL1unq4uroax44dO27p0qXfJSUliTdv3my13csnWgzaWG3cuJEkJyfz8+fPD/jxyo9U7aJ2eD9YrVZoXV2hdnGBh6enkJVsIyLlcjmeHzEcJ/NOgLNaBdMOQmA2mdA5IADjJ7zs+LQMHhKHzVtS4eysekxCQwhBi96AB1XV0Go0kMpl+Phva3Hl8mUMih0Eamu5tH7Y9lWE4zi4aFwwdOgwLHv/feSfPIlXE2dBo9WiXlePxkbBiHbosKHIO34cx7//AaUlJY6AAztzDgiasPr6euh0OpiMguOxVquFQqHgVq5IJruzsgwjho/IWb9+/Za0tLTeqamp38bHx7OpqamWtgCqNrVitdprWfdm7R296E+LtnTv0YMOih3EUFCHH5WPjw+WLF2C95cshUarQe8+fWDlrTCbzAgJC0XJ9euoqa6Gm231sMtgAmwT1wzDQOWkhIeHJ1QqFS5duoT+NvmL2WyGp5cXuv0uWJhoVghcWWVlJYaPGAGLxYL79++jqakZrq5CeLr9VGcfe5/x6kxcvHgRhefOAfg50sVuotvRuyNem52Euro6x+fWyckJEqnEkUTmyHc2WWAWmXH2zBn+yuUrfP7JfFFVZaUxMTFxbEpKSk5KSkrr+8a1pWfJtpULoZSSuLg4QilV/2HhH/ZUVVW5f7JhHWUZlmEI4/DwJAToGhyMu3fu4ML5C6CUYmBMDNRqNRhCcCI3F7W1dQiPEHw8HZHAPj54+PAhSktKUFJSgvLycnh5eeHO7QrU1NSgsLAQWlct/Pz8YDQJHJbFbEZ0/2jcKL0Bi8UCX39fEIZg99e7cCq/ACajCXYfewCOAMkWgwF5uXkoKipCbOwgaFy1ggrC1oNkWRbOajUUCgXsQVet439bjII0qEOHDjR7/35+6XvvsWKRmFEqlZfnzJnzanJyck737t0lgwcPRnx8/BPfT7XpFWv37t2M0H+19n3w4EHQiy+NsjqrnEWCsYegmVI4KcDzFI9qHmL02DFobtbDylnx7d+PwNfPF/0iIzF23DjU1tbCoNcLsWpU2PSqnFUYO34cgroEITBISIAtKrqG2MGD4e3tjUMHDyIr82v0+EuPx8INCGEQGRWJ6poaIS7ESSl4Xe3Zi20AXp4wAcs/WIHGxkYoFAoYDAYcyM7G7ydOxL179zD/9Xn4alfmY4HhlFJYbHaUrdtJdj93pZMS1dXVSN+5kxw+eIh94YUXsw4dOvQZgAJCiMXW/zMXFxejrZaorV6YXYBnT1BvamoSNFEGAziOQ89evdCnTzisnBVVlVVobGwEQxgEBAaiX3QUjC0tMJvMABUsiK4VXYOLiwuS5syG2WyGRCKBj68vjn//A/r27Ysp06bh0w0b0KI3OIKW7Ccxs9kMmUwGJ4UTah/VYtr06egXGYm/rvwz9u7Zg4GDYjDihZG4U3Ebf1n5Z5T/VI7PNm3CnTt3MHniJNy6eQvdQ3oIUzetTnut+Sh7k1wmk0Gnq6Nzk2bzLMsaxo8fv2vr1q1z7FEjbfGz16aBFR8fz9sUDxe8vLx+yt6XHRQ7eLDF19eXaTG2EALC8FSYHhZLxI6oN0IIfHx9HOGbnJWDsaUF+ma940EKU8YUnl6e0Ol0jtUhICAQaalfYNPnn2P0mDE2BQP/2ErC8cJcI2EYKJ2UABUCEfz8/WA2mVBWVgaL2YzvjnyLVX/5K6ofPMC6DRsgl8vh6emJjh07ory8HKG9wn715eE4Di2GFihVglmJVCbDsZxjvItaze7bv396796992/bto2llLIMw3Bt8bPX5umG5cuXE0KILjMzc6FOp9v71rz5Ym9fHxj0BgyOG0znvPE6Mba0/EOkrj3MSCqVgshtboGtEy54Cj9//8eihIUGuAgqZzVSN22CXq9Hp06dbBIaE+RyBRiWAccJYOvo4fnYibC+vh6R0VEYGBMDwjA4lpOD6gcP4N+pE0LDQoVWkEXICrx79x7EIrFjWqd1RqO9ee2YWSSEnjl9mnp6ejb36tXrIgBRVlYW/WfDkdpKtSm6ITk5mV++fDkzadKkA5mZmX0TExO/GjI47pSurq548+ebyNUrP/J249pfm/Wzr0Stba8pL5CcrSeb7cRnVVUVTp86BauVw9dfZaJDhw5gGAYGQ4ttn2bA3dt3oHJWwdPTAy3GFujqdbByVlg5K0xmk+DVAB4R/SLg7OyMe3fvovjaNRRdLcIrEyfB28cH0f2jodPpwDLC1JFEKnH4nQI/uwUqlUqkrFtvKb5WLOro7b2NEHI7NjYWCQkJTxWo2kxL57daPPZ9ltlslvTs2fNKU3Nz8O69ezhWxLIGWy506yxnuyS4qb4JJosJDGEcgU6t1Z12v/RPPvoYW9PSHNmCE1+ZhLcXLIBdmdnU1IRdX2ciNKwnovtHO8xGVE4q1DysBm/bbJeWlOLwwUPIOXoUAODr54vGhkb06tMHS5a+B0qFVVUqlWJbWhqGjxyJ/gP7o6GhEVabNkur1WL3rizLimXLxVFRUXsLCgqmJCQkWGwGabQdWP9e5QMJDw9nLly4YDly5MiL8+fPz3ZWq9lVa1ZTDw8Pxp5j3NpjSsjXMaL2kRA1IlfIoLVFqdhXMZ7noXBywoL5b+H4Dz8IJzYqKAxenjABcUPiUFlZia8zM3Gz/CY0Gg1GvDgSHTt6QyaVQqPVwtPTA3KFAocPHsajhw8R1T8a169fR2Z6hmPSetuO7fDz80NTUxOUSiWKiorw9vw3oVKpMOPVmRg1+iV4eXlBJpPhVH6+9Q9vLRB16dJl79mzZxNaEZ1PHajaNLB+GbOSnJxsTUtLG/X5559nV1RUsNNmTKfDR4wgZrMZahe1I0PHvgeqqqrC7YoKFF0tQnxCAtzc3R5r7EokElwruobMjAwc/e4oKKXo0aMHrl69CthmBXv26gV/f39k79/vSKtQqVRITduCwMBA3LlzBzqdDqFhoVAqlRCJRDiwPxvL318GiVSCbV9+Cakt3MnNzQ2HDx3Ch6tWQ6vVorGxESKRCFOnT4NUIuV2bN/OdunSZe/58+cTbNdI2wqL/swCqzW4Kisrw2NiYjaaTKZ+m7ek8gBhKU/honX5OTDbLKQ2sCIWly5ehK+vL7r36OEAFiEETY1CyLfKWYXPP92IjPQMZGR+hTt37qCyqgoBAZ3h7e2DvNxcbEz51HEdzz3/PNau+9hx4hRLJLDY/e0BqNVqnDl9BkVFVzFs2HNwUjiBFbOCNHnxYlTcuoV1KRsgFolxIPsA9u3ZY7FYLOLo6OiLBQUFEUTQC/FPM6jaNI/1a07N8fHxko4dO15Yu3Zt3Udr11KAUEIYWHkzDHphOocwQhKFWCyGWCJGUFAQ6hsaUFeng1wus01BW9BiaAFPeeib9Rg+YgS+yvgKO3fsRLfgbii/8RP27t4DzmqF3mBAREQE+g8cAJZlMSAmBhaLxdHGMRmNgh+D7WTX2NiIPuF9EBkVibLSMhw9ehRFP15FScl1PKypwdTp06Fv1sNsNiO8bziXd/y4WKPRmDdt2rSIEMJnZWWxTzuonipg2blESimzZcuWXaB05NeZmZY5c+cwHM+jvk4HlbOKsIQlMrnM0VvUurrCwllRef++EC5gO1XytNUJ0TYefywnB98eOQInJye8v3wZunbrCkIYePt4O7wX7M41diqjNeFp70Xa+4cAkLJuPUQiwb5o2YoV6NW7F9asXoP8kydBCGGjo6LLXhr90ryePXt+Hx8fzz6NJ8CnHlhZWVl8QkICk5WVtauwsPD3Bw4cGFl4rhBKlRI11dUICQnFkmVLHcZrIpEIzs7OtmRUIY1MIpE4bCGlUikYhnGMiNkPACtWJuOl0aMdDjQWswUN9Q3/EBhuby7zvOATKpFKHFJpVsTCZBJkxO8tXQKZXIagwCCIJRKER/TlTuXns9OmTTuxbdu2YYQQi23O8pkA1VMHLJtcmSeEGCmlY7t37/5aeXn5bLsn/M6dOwP1er1i1ZrVVKFQEINeyJ+WSqUwGo0Q21zudDodzhcW4mb5TYGLamzClq1puHq1CNeLiwUHGVuApcO0w8aD2R2U7XOGjY2NaDEIOTxaqdbBpUnEwsQNy7II6toFFTdvAba9Xb/IftTbxwcqleoGIcQSFBQkTUhIMOEZKtFTd9oQwEUIIWYAnykUis/sJ8FFixZtWLly5fy33pjP/XHxuyK1Wu2QzhBCUF5TjrQvvkBx8XV4enig/8AB6N6jO0JDw9ChQweo1S44efIEblfchl8nP+ib9Q5AiUQiqFQqNDQ04IvNqbhRVoaZs2YJ8W+2LGo7MWvXadXVCjmLly5cROfOAWBFggWm0kkJAJzJZNJSSknfvn15PGPFPI0XbQdXfHw8azAYiF6vZ41GI8nOzl6n0WhQWFjIfrL2Y0cogcVigVqttmU2H0Pl/fvw7+SPdxcvRnR0f4jFYjQ0NEClVuFGaRmWvrcEzY3N0Gq1UCqVgpepxYL9e/dhxtTp+GJzKnKP52LN6g8hlUodBrVyuVwYUlUoYDKZcOniRShVKlitHO/q5srJZTLezd2dP3LkCK9vbmY1Gk0GIYQGBAQ8c8Aiz9ALws+cOTN2165duSaTiXIcR958+y1MiI8XoktKSzEnMQkhoSFwUjjh8qWLWP/pp+jdp7fAKbGCG96cpNkoPHcO3bp1w+Spk8HzFFeuXEFx0TWUlpYCAF5LTMSg2FhMmzIFcUPi8PtJk2CxWKibmxt8fH0IZ+WwetUqHDuag8FxcdyNsjK2vr4enTp3BsdxeFBVhYiIiIPffPPNywkJCfRJjMC31z/JcQHA+vXrs1xdXemy5BWWyKhICoAGdelCI/pFUEII9fLyohm7Mmlq2hYKgHdzd7cc/vbvXPGNUlpyo4wmr/yAAqByuZzaGO/H/vUJD6eBQUE0bsgQWlxWQtdtWE89vbwe+z/BvwvmPD08OIVCwXXp2tWq0Wjoc8OeuzZlypTU2bNnl8yaNev6/Pnz36CUip6xl/vp3mP9d2WxWGRSqZSLio5CZFQkzp4+i6KrV2E0GvH6vDcwdNgwOKudUWGoACEEBr1eNCdxNua+Phfl5eXY8eV2dOrcGXPfmIuKWxU4/sNxVD94gMCgQLwyeTIio6JgMBiQkZ6OtX/7CBPi4xEfP4Fu/HQjGThwYA3P86L8/HytRCJBYGAg7t27h+Dg4H1Hc45OlMvlFrFYUDg0NzcjJSUFtr0ifRaB9Uy8LfajekZGxuSFCxemD31umHnuG6+LbPG6vL5ZTzUaDcOKWNLU3ERTPtmA748ds86bN++d06dOvZ174kQQAMQNicPCRYtQU1MjxIaIxaC2tFhnZ2c0NTWBIQQSqRTnz5/HrZs3cSznmOV2RYVo69atq8PCwjZ98MEHh9PT0yUqlYoZNWrU+Z07d0620RQOb/XY2Fg2NzeXe1ZB9cwAy5blQ1asWCFKTEw8dOjQoefd3N2gcHLC7VsVDilNYFAgGhoa0dTYiGHDhn24Y8eOxTzPewwaNOheQUGByL9TJ/rqa7NIQOfOeFBdjeBu3eDu4QGj0ejQqlPbiU8kkUDp5ISzZ85aFi1cKE5LS1sxfvz4ZJlMBqPR6GDiW/knPLMgepY3747PCqVUtmbNmjdKS0rnMixDqqqqDre0tFzy9fUdrVAowhp0uvrOgYEfrlq1ajfP8yJKqefUqVNvpaeni6RSKTWZTCS8b7igEvXzx9hxY+Hn7//Y37JarfYpZG7+vHnsw+qa5jNnzvgmJSU1/ULmwrTaf7XX0wwu+89qtRouLi4OzZZMJoNGo4FKpXJoviilhFKqGTBggMXf359mZH7FT546hf5pyRL6pyXvUQB0ytSp9ErRVZp/uoCeKTxH808X0POXLtL9B7K5sLAw6uHhYXjnnXcG2f420/4UnmIe63/it2JjY0UNDQ2or6+H1WplY2NjRUajkdHpdGhqakJsbKwIAEMIodu2bRtZUlLCTEhI4Hz9/MiLo0bBz98PQ4YNRe8+vXHxwkVHCqrVYoFMLoOuTscnznqNaTEYjEuWLBm+du3aEwkJCf/xfJp2YD1hcOXl5bXWLnO23x0PPTc3lwPAU0pdDmQfSNbpdExIaAjR6/VQyBVobGzE7du3EdqzJ4qLr+HQwYPU3cOdV6nVVC6Xc8uXLWPUarXxy+3bh7/55psnk5KSxO1c1DNMN/wL4CMA+JaWFuXJU/lBPUJCIJPJGEIIJFIJggIDUVBQgO9zjgEAlv7pPXKjtIz07ReBHV9uZ+/cvt0yY8aMEQMGDDgRHh4uTk1NtbRDCW1zEvoJHFroo0ePlPfv3XszLCyMjYqOgsSmQhWLxQgODoZEIqaF587RcePGWY/l5FTt3b2nwdPdvW769OkTVq5ceSIpKUl8+PDhdlC1r1iP14Bhw3Cr/CZDQeHh6ekIiLIn0VutHHVzc2PS09MHy+XyU7NTZ7ObkxxuLkz7SvX/aI/1r1TJpUtgRCwdPGQIRCKRY95PpVKhuLiY27plCxMWFrZdoVCcJITQ1NkON5f2jXo7sH679Ho94TiOqJ2dKcMQxzdSpVLxO7Z9iQ5abdV33333qu0+teb82kHVDiz8VqQduXz5sjWibwT5bONnhFLwLi4utKO3N83Ny7NcLy5mnxs+/CMANCkpiW0HU3vhn00do5SSrVu3jgkICORDQkNoymcb6VsL3qYarZZGRUXtpJSKbQcc0n7H2utfmrgGgPT09DExMTHVAKpcXFxqEhISdkqlUvuXsR1U7fW/BxelVOrv7y+jlMokEgkAkNYtovZqr3/HXrMdUGhXN/wn7kW7GqG92qtNvqWrVq3SaLXa5tmzZ7ezyO31f67NmzeL6+rqlIxSqQyuq6tTtt+S9vp3VF1dnVKpVAb/F3DzxmtXlQi7AAAAAElFTkSuQmCC", "cyp3a4": "data:image/png;base64,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", "cyp3a4_dead": "data:image/png;base64,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", "quinidine": "data:image/png;base64,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", "ritonavir": "data:image/png;base64,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", "rifampicin": "data:image/png;base64,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", "felodipine": "data:image/png;base64,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", "metoprolol": "data:image/png;base64,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", "nirmatrelvir": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD0AAABECAYAAAAyTz3gAAAR80lEQVR42u1baXSU5dm+nud933knM5NMQjYSSAIJBAiEsMSE1RhQNsEFHY7LB7EotCroJ57WshzDVAT8sNUcbBFQKvBhS6gWrIIsmiCyQ1TIQgKEECAr2SbJbO9yfz+ylFaR4AcppdznzJn8mclc771d93U/D1u9erWkKEr4nDlzzgNgAAi3nzEA9M4770RJklTGHQ5HuKZpawEgKytLuA0Bt+PSNG2tw+EIx3+qsdWrV0v/CUBbcTLcsTt2x26aEREjInYdref/bWJnAszMzGxviXl5eZSfn88YY1oreHNeXl5YaWlpzvz58/Xc3JNc03QEBQZqry1ZIiQkJIwcMWLEyczMTGHatGnaLe/N9PR0EYBwFU+HfvzxxzEfffRxw4SJE4lxTowxYoyRZDBSK1miyZMn0/Lly+P/+eHdiqRAtNlshisAjiaiUUQ0+syZM2Nff/310evWrcufNXs2AdDbAHJBJEGUaPjUmTT80adJNlkIgD5u3DhasGDBEAA4duyYdMuFd1ZWlpiamqoCQHZ29gNbt24NX7NmzarGxkZIkoTq6mocP34cO3bsAADVr0uwaA3tjvqqMjTWVIKBobasFKMf+wUY4ziwZS127dqlCoJw/ODBfamJiYnZt1Sob9++XW717JS0tLRfP2qz0aBBgwmAG4DnyhdjTBuYOoVmLF1P8zYdoJm/3UyJ9z9BYmtoW4PD6e7Hnqfw3vEEQPMxmZT58xc0E9HU9PR0IxFdd6jf8NzIyMiQp0+f7tm3b9+UtWvXbtrzxReTvtq711tRUaEyQJYkSRBEUZBESdA1VRg0/lH24EtvoGuv/hBEEcGRvdB3xL0w+JhwqegEmmqr4BfUFckPzkBjbSW7fLFEPXv2rFHXdfOiRYs2WiwW0+7du5V/GejVq1dLzz//vPfAgQMTNm7c+L8r33nHUlVZ6Q2JiJbjRk0UDT5m1FVdAhFBVRQER8bg/heWwOwfBHdzA8AYvG4nSNMQFZ8Evy4hKDlxBMFRvZA0ZTpihoxGVUkBv3CmQMnNzbfMnPmzyiVLluTYbDZDfn6+1uk53ZpfSnZ2duqmTZv+tHHjRquqKHr8PZONo6Y9C8FgQG7W31B2+iQ8bid6DR2NuyY/Cb+AYGiqF4LYUpcEUQKRBtXjRv+UyagsKQRjAEAIjozB5BeWso/feFGsu1gcUVNTt2b//v36yJEjN19ZQzoFdCtgnYiSV61a9en7779vcrvder8R9wnjZi2ENSQM53OPwtlQi36jJ6BP8lj0TEiGweQL0PfHd8YEaJoK2eyLyAF34XLpGei6Bq+rCaE9+2Lic4v52v+2ubOyvjBXVVVEEhESExM7TFz4jQC9ZcsWAKAFCxYYt27bZnK73Z6eCcn8vmfmwxocBqejHo2XKxEZfxfGz1qIuNETYbRYWwgWYz/Uu8E4h65paLpcAZO1C0RJBoFB8TgRHNUbQ8c9bCwrK3NPnDRpKYCHjx07pmZlZYmdDRp//vOf9ZzjOWCMsZghoxEUEQNV8aKpthpm/yDEjRoPo8UXmqpA1/WrijSMC5CMPqi5WIzS/BxY/AMhyjJABF3TYDCa4B8WCTCGI0ePCe+9914jY4yys7M7z9NtVl5ejvr6OoAx+IV0gyCJIOhwNzcgNKYvGBdAdA01Stehed2oPncah/+6Hv6h3RAZNxSk6+2fZYIILkgAkbD9s8/0ffv2pTgcjuCO8vMbCjo1NVXv07efAiJ4mh3gTABpOvyCukKSfa4JmEhHxblT+OpPv8fHK15GVWkRYpPHQPIxQVOUdjSkazD7B8EgGyVHQ73COV+4ePHiALvdrqanp3cO6MzMTADAzJkzjSkpKRIRUcWZXDgddRBEsUNSY1sOf7PrLzj40TpUnivAwLEPIqxX/xbAjAGs5ee6GuoRPWgE7n5yLsx+/uKGDRu8/fv3n09EVrvdTtea2m4IaJvNpttsNiEhIeFEedmld8xms1RwYLdSsH8nZJMFjtoqqF7XNUFfOvUdTn65DariQVD3GETGJYKBgXS9peARQVNVcFGAX3AYkh6Yge59EwRd14XYPn2eAuDfETX3hoBmjFFcXByLjY2tnjBhwuf33ncfdzrqtayNb+O7rG2QZBnVJWfArpJujDEoLicKD+4BEcESEISQHn2gaxr01koOIhBa/pZkH5Cuw9PsgK63cBLFq6Cj8jW/0YJAbGxsF3+rFYwxVltWgp3vLkHZqRNobqjFhYKcdpAtrYqBMYAJAoq/PQhd15A46TH0HX4vfAODUV9VBtXrBmMt3mYAOOfQVRU+vlZcyM/B2W8OebuGhQlbt/51KoAyAJwxRp0COjk5WWCM0T333NPco0cPEBEkyYD6ykvI378TRAR3kwMXC76B19UM0jSQrkLxeHAxLweq141+I8dh6MTHEDUwGUWHv8T+zatQff40RIMMLkoAY2CMw2TtgvO5R7F300odpElPPvmk8sQTTxQyxtT09PTO4d4pKSni0qVLFUmSkJCQMH7Hjh3ji4qKdMaYoOs66itKETUwCeG9B0CSZTiqKwAQVLcLtWXnIZt9ERbTD0ERMSAGHPzofZScOIL6qku4WPANzP6BMAcEQRAlaJqKi6eOY+ubv9RqLxbz1LFjm3pERU2eMWPG0ezsbHH9+vXaTaehx44dkxITExUiGvXaa68N3bRp01vbtm1TJMlgUBQvTP7BCOwZB1djPTRVQdeYOOiq0pJ8BPiFhLW3MsXtxMmsv6E4Z39LCgCoKinC5teeVyIGJFLvIaNQVVKE3K+26wCkMWPGOIYlJz+xZMmSL0VRFPfu3at2mtC2ffv2tMLCwg9WvfsuigoLtbYICuwRh6G2FxAUHQeTuwpcFBDSow8Y4+2gWgpUS547aiqxP3M1jn66CZwL7UXK6h+AJkc9NL3l4QwYEI+EhISmuLh+0xcuXLg1PT3dYLfbvTd9yiIiDkAoKSmZtXDhwt9/+OGHHgDc6Osn+fkHQbaGIG7y0wiOHgBNcaN7v8Ht3jZcQVQIgCgKEDiHyeQLl8vVXuwYY1q3bt2E8PDwTWeKiy80NjZyVVXVcePuE15++eXD3bp125qRkSG/+OKLnuvd5v0kmz17trRmzRrlD3/4Q+Nzzz0nSwaDOOCeB9jgex+Go6kZHsEX1rAoqF4vGAdiIkLax8c2Ssk5hyQKqLzcAEXToWsajvxtA05+8h4YaVBV1fP000/Lb7zxRlxQUFAB57yVs/9dcLTb7So6QyMjIpExpubnn3rz4Ycf1ARBEAIjerH759hh8gtATVkpKuqaoSgKBM7bhwgiHQADAZAkCbV1jWhsdsPl8UBVdQiShB5DU3EhJxt1JfkAwMxmM7777rswAMVJSUn80KFD2oQJE9grr7yidXR+viEtKy8vjwMgzjFBVVWrpmnoM2wsVMWLi4UnwEDoFR0JH1mEqmpXhBNraWWigDpHMyouN6DJ5QbAIEkCOACTfyhCeg+C3hr+uq5DlmUFgGfevHleAN7PP//c81MB/2TQBoOBEREnxuoFoeUrai6cxekje6G4mmHyCwBjQPeuQYiNDoMgCO1agSAIqHc4UVZZC84ZREFoq2fQNRUGHzO6xg5uf1CiKOpGo/GGHhTg18u4MjMzhdjYWC9jTIeuU1tZOH1sLxjn6NqrP4gx6DpBEBgEQUCPiGBwzsA5R5PTg4sVtRC40C4YXPEfAM7BBREEeMLCu4nZ2dnThw4duj8lJUW8UXIvvx7AjDGaNm2aRkQhRJTwySefWOrr68EYh39od/QaOgpcEK74zPdBkaa2DBCkt77TPygmuqpA8TQCAA1NTOTTp08XW5neDfO02NH2xBjTicj30qVLKXa7/bm7kodNXL9hI6qqLwOk89jkMbAEhcLd5ADnVyF61FJ5JZMFEmegVlbWQlYIRos/vK5mnN33qQ4AJqOcl5qaeh4A79+/P3Ua6FYP60TENm/evDI3Ny9t2bKl0DRNASABQGiPWCSMfQiKy3V1wCBw0QBPUwXOHdgDH79AyGZfdInsA0uXEOi6jroLRbhwfA8u5R12xcfHmwMCAjcMGTJk79y5c+Vp06Z5OgV02zBORMG7du3KeOuttx4/fPiwUzIYjX1TH5GYZIS7qQ6JqZMQFBHzDz30e3nERTTVXcZXG95E/lfbIZmtqsFkYaG9EwSTfxCICJWFOag4fcLp4+NjHj58eMGcOc/tj4vrK4eFhakrV67snPBupYpUXl7uPHT4yOOHDx92h/caaOo35RmE9hkMSTZB9TgREWptpYzsal8EMIbTR/biZPanLWK/o1Z0OWrRUFGqXnmU6+6Ue0xjx6Se03X90fj4+HybzSZs2bLlhu6rxGtHNxm2bt365bJlSxWjxVeOGjUFPZPuQ/PlcnhVBwgMomxsEzau+vBUxYvy0ydBRErfvnGSwWh4I23GjOjY2D62yspK+Pj4oKamxlt89szdr776aiVjrKhtmLnRq6eOFDJutfonuV0uhPYeiIhBd8NZU9miaRFD9/Au4Lg64CuLmNvpAAAymYyYNGlS5byXXnoVwKsAvK3eVhhjpW+//TZsNptwMwB3uHo7nU6Fcy4JkgxRNoE0DYwxcDDIktSibPwIatJ1iJKMEbafo66s1JCTc9wriOL/1NTU1K9ateqP/6S3CXFxcWS322/aCrZDfdpkMkm6rkNTPFA9TjDO4fWq6B4eCEnqgJYNQNMUhMXE4dFFKxE9aLjh6JEjOHHy5Lrly5f/jIjM6enpIhGxLVu2aHa7Xb+Zq+SOgNYbGuqPGH18lIbyc3Th26/g4xcIg8TBWQfCuj2vObwuJ6wh3TH1lbcQnZAs7v/6a295efm69evX+9vtdnXx4sWdcrCNX1voZN5hw4aNmT9/geRuavSc+3obinOyERUVAbPJB5racd7POIenqRFBETEY/sgs+Fj8hDVr1qguj+dxIpLtdjv9y0ETEYiIde3a1TQsOelPSUlJxoozuc4DaxbqOZ9thKJ4IErSdR0c5qIIp6Me4bEDEN67v+ByufjgQYNWALC2ftFN9/a1+jS1MrJqInrS4/F4t2/fkfbuu6uwc5VdrzyTy8c982uY/AKg03WkYVvha1NP/i6idIqJHRHyr+Dec61W65bC00XPF506NfHb3R8ploBAaezMV1oc1IEE1zUNvtYuKDy4GxcLT2oWi4UdPnrk2WHJSQ2ddd6cd3CDobd6vDElJeWzlRkZ/zV69Og9IaGh4qG/fqBVnM2FIIg/tGr+XuuSDDLqyktxcs9H8LiatZ//4hc8Ijz8U8aYtyPLt04dLdtCfefOneYBAwbULlu2tCK6Z09SFS/tXr8SxReqUV5VD85/vGeLBhkF+3ei4NCX3rCwcLH47NlpU6dOrQYg3OxW9ZNEBMYYjR8/vnnu3Llyjx49nxo+fHiuxWwSio98oZfnH0K3rkEAE34wQokIXJTQXF+DSwU5IF3XZ6TN4IsWLapljHnaNp+3HOg2S0tL0xlj2pw5c769KymZAaTu+u0LyoG/rIHq9UAQxHbN+kpFgQsC3M0OVJUUEQCEhYWdHzJkiBMAs9lsdEuDTkxMVDIzM4WYmJi0p5566r2HHnrIIMtGaefa5conv/slGmsqYZBN0BQviFqkXaKWfD6X8zUuFJ5wDho02Lg3+4tXGWMHbTabxBjTb5nqfTVrlY1ExtiskpKSxoKC8d0UVZ12IutTj6e5SZ7y0nIEdo+Gu7kRgizCaLLgm11bsGf97xSrv795xIgRhS+/PK94woT7pYCAAK3t3Mq/hWVkZMgAIMsyfvWrX/3x7pQUAuDuOTCZHv312/TSxn307KrP6N60eWQJCFJ8jEZ9ypQHzjz77LMD2wYM4N/zCpARgEREfN26de+NGDmSADhFyaCGx8YrQd2jldazoNrURx65+Jvf/Ca+dUNhwL+zpaen85SUFJGI5B07dnzw+tJlZLVa289rjxg5ilaseLNm5cqVsW1rIeD2uJrAW9+NlZWVMZGRkT1lv+AY2WqNnj17dgwRhV9x6B231Z2Ma0UEblNru4zyD6/ruKByx+7YHbtzwRR3Lpj+mK1YsSIqIyNjV9u1Ityel8bFVsq8a8WKFVHcz8+vTBCEWQCQmpqq3Y6g23AJgjDLz8+v7P8A91d8MrFKauAAAAAASUVORK5CYII=", "isavuconazole": "data:image/png;base64,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", "paroxetine_med": "data:image/png;base64,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", "paroxetine": "data:image/png;base64,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", "simvastatin_med": "data:image/png;base64,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", "midazolam_med": "data:image/png;base64,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", "isavuconazole_med": "data:image/png;base64,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"};
const ICONS = {"pill": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M219.26,36.77a57.28,57.28,0,0,0-81,0L36.77,138.26a57.26,57.26,0,0,0,81,81L219.26,117.74A57.33,57.33,0,0,0,219.26,36.77ZM100.78,202.26a33.26,33.26,0,1,1-47-47L96,113l47,47Zm101.5-101.49L160,143,113,96l42.27-42.26a33.26,33.26,0,0,1,47,47Zm-9.77-25.26a12,12,0,0,1,0,17l-24,24a12,12,0,1,1-17-17l24-24A12,12,0,0,1,192.51,75.51Z\"/></svg>", "syringe": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M240.49,63.51l-48-48a12,12,0,0,0-17,17L191,48,168,71,136.49,39.51a12,12,0,1,0-17,17L123,60,41.86,141.17A19.86,19.86,0,0,0,36,155.31V203L15.51,223.51a12,12,0,0,0,17,17L53,220h47.72a19.86,19.86,0,0,0,14.14-5.86L196,133l3.51,3.52a12,12,0,0,0,17-17L185,88l23-23,15.51,15.52a12,12,0,1,0,17-17ZM99,196H60V157l14-14,17.51,17.52a12,12,0,0,0,17-17L91,126l11-11,17.51,17.52a12,12,0,0,0,17-17L119,98l21-21,39,39Z\"/></svg>", "drop": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M134.88,6.17a12,12,0,0,0-13.76,0,259,259,0,0,0-42.18,39C50.85,77.43,36,111.62,36,144a92,92,0,0,0,184,0C220,66.64,138.36,8.6,134.88,6.17ZM128,212a68.07,68.07,0,0,1-68-68c0-33.31,20-63.37,36.7-82.71A249.35,249.35,0,0,1,128,31.11a249.35,249.35,0,0,1,31.3,30.18C176,80.63,196,110.69,196,144A68.07,68.07,0,0,1,128,212Zm49.62-52.4a52,52,0,0,1-34,34,12.2,12.2,0,0,1-3.6.55,12,12,0,0,1-3.6-23.45,28,28,0,0,0,18.32-18.32,12,12,0,0,1,22.9,7.2Z\"/></svg>", "arrow-counter-clockwise": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M228,128a100,100,0,0,1-98.66,100H128a99.39,99.39,0,0,1-68.62-27.29,12,12,0,0,1,16.48-17.45,76,76,0,1,0-1.57-109c-.13.13-.25.25-.39.37L54.89,92H72a12,12,0,0,1,0,24H24a12,12,0,0,1-12-12V56a12,12,0,0,1,24,0V76.72L57.48,57.06A100,100,0,0,1,228,128Z\"/></svg>", "arrow-right": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M224.49,136.49l-72,72a12,12,0,0,1-17-17L187,140H40a12,12,0,0,1,0-24H187L135.51,64.48a12,12,0,0,1,17-17l72,72A12,12,0,0,1,224.49,136.49Z\"/></svg>", "squares-four": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M100,36H56A20,20,0,0,0,36,56v44a20,20,0,0,0,20,20h44a20,20,0,0,0,20-20V56A20,20,0,0,0,100,36ZM96,96H60V60H96ZM200,36H156a20,20,0,0,0-20,20v44a20,20,0,0,0,20,20h44a20,20,0,0,0,20-20V56A20,20,0,0,0,200,36Zm-4,60H160V60h36Zm-96,40H56a20,20,0,0,0-20,20v44a20,20,0,0,0,20,20h44a20,20,0,0,0,20-20V156A20,20,0,0,0,100,136Zm-4,60H60V160H96Zm104-60H156a20,20,0,0,0-20,20v44a20,20,0,0,0,20,20h44a20,20,0,0,0,20-20V156A20,20,0,0,0,200,136Zm-4,60H160V160h36Z\"/></svg>", "pause": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M216,48V208a16,16,0,0,1-16,16H160a16,16,0,0,1-16-16V48a16,16,0,0,1,16-16h40A16,16,0,0,1,216,48ZM96,32H56A16,16,0,0,0,40,48V208a16,16,0,0,0,16,16H96a16,16,0,0,0,16-16V48A16,16,0,0,0,96,32Z\"/></svg>", "play": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M240,128a15.74,15.74,0,0,1-7.6,13.51L88.32,229.65a16,16,0,0,1-16.2.3A15.86,15.86,0,0,1,64,216.13V39.87a15.86,15.86,0,0,1,8.12-13.82,16,16,0,0,1,16.2.3L232.4,114.49A15.74,15.74,0,0,1,240,128Z\"/></svg>", "star": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M239.18,97.26A16.38,16.38,0,0,0,224.92,86l-59-4.76L143.14,26.15a16.36,16.36,0,0,0-30.27,0L90.11,81.23,31.08,86a16.46,16.46,0,0,0-9.37,28.86l45,38.83L53,211.75a16.38,16.38,0,0,0,24.5,17.82L128,198.49l50.53,31.08A16.4,16.4,0,0,0,203,211.75l-13.76-58.07,45-38.83A16.43,16.43,0,0,0,239.18,97.26Zm-15.34,5.47-48.7,42a8,8,0,0,0-2.56,7.91l14.88,62.8a.37.37,0,0,1-.17.48c-.18.14-.23.11-.38,0l-54.72-33.65a8,8,0,0,0-8.38,0L69.09,215.94c-.15.09-.19.12-.38,0a.37.37,0,0,1-.17-.48l14.88-62.8a8,8,0,0,0-2.56-7.91l-48.7-42c-.12-.1-.23-.19-.13-.5s.18-.27.33-.29l63.92-5.16A8,8,0,0,0,103,91.86l24.62-59.61c.08-.17.11-.25.35-.25s.27.08.35.25L153,91.86a8,8,0,0,0,6.75,4.92l63.92,5.16c.15,0,.24,0,.33.29S224,102.63,223.84,102.73Z\"/></svg>", "star-fill": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M234.29,114.85l-45,38.83L203,211.75a16.4,16.4,0,0,1-24.5,17.82L128,198.49,77.47,229.57A16.4,16.4,0,0,1,53,211.75l13.76-58.07-45-38.83A16.46,16.46,0,0,1,31.08,86l59-4.76,22.76-55.08a16.36,16.36,0,0,1,30.27,0l22.75,55.08,59,4.76a16.46,16.46,0,0,1,9.37,28.86Z\"/></svg>", "info": "<svg viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\"><path d=\"M108,84a16,16,0,1,1,16,16A16,16,0,0,1,108,84Zm128,44A108,108,0,1,1,128,20,108.12,108.12,0,0,1,236,128Zm-24,0a84,84,0,1,0-84,84A84.09,84.09,0,0,0,212,128Zm-72,36.68V132a20,20,0,0,0-20-20,12,12,0,0,0-4,23.32V168a20,20,0,0,0,20,20,12,12,0,0,0,4-23.32Z\"/></svg>"};
const Physics = (() => {
  const ABSORB = 1.6;
  const OVERDOSE = 0.92;
  const GRACE = 2;
  const PILL_COOLDOWN = 0.6;
  const DEFAULT_TURNOVER = 0.045;
  const TEST_DURATION = 2;
  const INJECTION_RATE = 3;

  function randomIn([low, high], random) {
    return low + random() * (high - low);
  }

  function scheduleEvents(level, random) {
    return (level.events ?? []).map((event) => {
      const start = randomIn(event.start, random);
      const stop = event.length ? start + randomIn(event.length, random) : Infinity;
      return { ...event, start, stop };
    });
  }

  function newTank(spec) {
    return { level: 0, pills: [], lastPill: -Infinity, inBand: 0, paused: false, nextAuto: spec.auto?.offset ?? 0, injecting: 0 };
  }

  function createState(level, random = Math.random) {
    return {
      time: 0,
      enzyme: 1,
      block: 0,
      random,
      tanks: level.tanks.map(newTank),
      events: scheduleEvents(level, random),
      boostersLeft: level.boosters?.count ?? 0,
      injectionsLeft: level.injections?.count ?? 0,
      testsLeft: level.bloodTests ?? 0,
      revealUntil: -Infinity,
      outcome: null,
      overdosedTank: null,
    };
  }

  function activeEvents(state) {
    return state.events.filter((event) => state.time >= event.start && state.time < event.stop);
  }

  function pillReady(state, index = 0) {
    return state.time - state.tanks[index].lastPill >= PILL_COOLDOWN;
  }

  function addPill(state, spec, tank) {
    const variance = spec.gate ? 1 + (state.random() - 0.5) * (spec.gateVariance ?? 0) : 1;
    tank.pills.push({ remaining: spec.dose, age: 0, variance });
  }

  function takePill(state, level, index = 0) {
    if (state.outcome || !pillReady(state, index)) return false;
    const tank = state.tanks[index];
    tank.lastPill = state.time;
    addPill(state, level.tanks[index], tank);
    return true;
  }

  function takeBooster(state, level) {
    if (state.outcome || state.boostersLeft <= 0) return false;
    state.boostersLeft -= 1;
    const effect = level.boosters.effect;
    state.events.push({ ...effect, drug: level.boosters.drug, booster: true, start: state.time, stop: state.time + effect.duration });
    return true;
  }

  function giveInjection(state, level) {
    if (state.outcome || state.injectionsLeft <= 0) return false;
    state.injectionsLeft -= 1;
    state.tanks[0].injecting += level.injections.amount;
    return true;
  }

  function takeBloodTest(state) {
    if (state.outcome || state.testsLeft <= 0) return false;
    state.testsLeft -= 1;
    state.revealUntil = state.time + TEST_DURATION;
    return true;
  }

  function togglePause(state, index) {
    if (state.outcome) return false;
    state.tanks[index].paused = !state.tanks[index].paused;
    return true;
  }

  function isRevealed(state, level) {
    return !level.blind || state.outcome !== null || state.time < state.revealUntil;
  }

  function sumOf(events, key) {
    return events.reduce((sum, event) => sum + (event[key] ?? 0), 0);
  }

  function competition(state, level) {
    return level.tanks.reduce((sum, spec, index) => sum + (spec.compete ?? 0) * state.tanks[index].level, 0);
  }

  function updateEnzyme(state, level, active, dt) {
    const targetBlock = Math.min(0.95, sumOf(active, "block") + competition(state, level));
    state.block += (targetBlock - state.block) * Math.min(1, dt * 3);
    const target = 1 + sumOf(active, "induce");
    const turnover = level.turnover ?? DEFAULT_TURNOVER;
    state.enzyme += (turnover * (target - state.enzyme) - sumOf(active, "kill") * state.enzyme) * dt;
  }

  function capacity(state) {
    return state.enzyme * (1 - state.block);
  }

  function throughGate(state, spec, variance = 1) {
    return Math.max(0.05, 1 - (spec.gate ?? 0) * variance * capacity(state));
  }

  function landingTime(spec) {
    return spec.gate ? 0.55 : 0.3;
  }

  function autoDose(state, level) {
    level.tanks.forEach((spec, index) => {
      const tank = state.tanks[index];
      if (!spec.auto || state.time < tank.nextAuto) return;
      tank.nextAuto += spec.auto.period;
      if (!tank.paused) addPill(state, spec, tank);
    });
  }

  function absorb(state, spec, tank, dt) {
    let entered = 0;
    for (const pill of tank.pills) {
      pill.age += dt;
      if (pill.age < landingTime(spec)) continue;
      const amount = pill.remaining * Math.min(1, ABSORB * dt);
      pill.remaining -= amount;
      entered += amount * throughGate(state, spec, pill.variance);
    }
    tank.pills = tank.pills.filter((pill) => pill.remaining > 0.004);
    const injected = Math.min(tank.injecting, INJECTION_RATE * dt);
    tank.injecting -= injected;
    return entered + injected;
  }

  function inBand(tank, spec) {
    return tank.level >= spec.band[0] && tank.level <= spec.band[1];
  }

  function stepTank(state, level, index, dt) {
    const spec = level.tanks[index];
    const tank = state.tanks[index];
    const entered = absorb(state, spec, tank, dt);
    tank.level += entered - spec.drain * capacity(state) * tank.level * dt;
    if (state.time > GRACE && inBand(tank, spec)) tank.inBand += dt;
    if (tank.level >= OVERDOSE && !state.outcome) {
      state.outcome = "overdose";
      state.overdosedTank = index;
    }
  }

  function step(state, level, dt) {
    if (state.outcome) return;
    state.time += dt;
    updateEnzyme(state, level, activeEvents(state), dt);
    autoDose(state, level);
    level.tanks.forEach((_, index) => stepTank(state, level, index, dt));
    if (!state.outcome && state.time >= level.duration) state.outcome = "done";
  }

  function score(state, level) {
    const total = state.tanks.reduce((sum, tank) => sum + tank.inBand, 0);
    return total / (state.tanks.length * (level.duration - GRACE));
  }

  return {
    OVERDOSE, GRACE, PILL_COOLDOWN, TEST_DURATION,
    createState, step, takePill, takeBooster, giveInjection, takeBloodTest, togglePause,
    pillReady, isRevealed, activeEvents, capacity, throughGate, landingTime, inBand, score,
  };
})();

const WORLDS = [
  { name: "The drain", enzyme: "cyp2d6", enzymeName: "CYP2D6" },
  { name: "Two prescriptions", enzyme: "cyp2d6", enzymeName: "CYP2D6" },
  { name: "The gatekeeper", enzyme: "cyp3a4", enzymeName: "CYP3A4" },
  { name: "Paxlovid", enzyme: "cyp3a4", enzymeName: "CYP3A4" },
  { name: "Blind", enzyme: "cyp2d6", enzymeName: "CYP2D6" },
  { name: "A week on antifungals", enzyme: "cyp3a4", enzymeName: "CYP3A4" },
];

const STANDARD_BAND = [0.4, 0.66];

const LEVELS = [
  {
    world: 0, title: "Find the rhythm", duration: 14,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: STANDARD_BAND, key: "Space" }],
    tips: [
      { when: "start", anchor: "tank", text: "Tap the beaker to take a pill", until: "pill" },
      { when: "time:2.5", anchor: "tank", text: "Keep the water inside the green band" },
      { when: "nearTop", anchor: "liver", text: "Wait while the enzymes drain it" },
    ],
    learned: "drug clearance", reveal: "Liver enzymes remove medicine from your blood, so doses have to keep coming.",
  },
  {
    world: 0, title: "The slow one", duration: 22,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.12, dose: 0.3, band: STANDARD_BAND, key: "Space" }],
    tips: [{ when: "start", anchor: "liver", text: "These enzymes clear this medicine slowly" }],
    learned: "half-life", reveal: "A medicine that clears slowly lasts longer, so it needs fewer doses and forgives fewer mistakes.",
  },
  {
    world: 1, title: "Two prescriptions", duration: 36,
    tanks: [
      { medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: STANDARD_BAND, key: "Space" },
      { medicine: "paroxetine", label: "Depression", drain: 0.22, dose: 0.3, band: STANDARD_BAND, compete: 0.9, key: "Digit1" },
    ],
    tips: [
      { when: "start", anchor: "tank", text: "Tap a beaker to dose it" },
      { when: "time:4", anchor: "liver", text: "The depression pill also jams the enzymes" },
    ],
    learned: "drug interactions", reveal: "The depression pill blocked the enzyme that clears both pills, so both built up.",
  },
  {
    world: 2, title: "The long way in", duration: 32,
    tanks: [{ medicine: "felodipine", label: "Blood pressure", drain: 0.3, dose: 2.0, gate: 0.85, gateVariance: 0.7, band: [0.38, 0.7], key: "Space" }],
    injections: { count: 8, amount: 0.18 },
    tips: [
      { when: "start", anchor: "gate", text: "The liver takes an unpredictable bite of each pill" },
      { when: "time:4", anchor: "tokens", text: "Injections skip the liver and give an exact dose" },
    ],
    learned: "first-pass metabolism", reveal: "Swallowed pills pass through the liver before your blood and lose part of each dose there. Injections skip it.",
  },
  {
    world: 2, title: "Hit twice", duration: 34,
    tanks: [{ medicine: "felodipine", label: "Blood pressure", drain: 0.3, dose: 0.7, gate: 0.5, gateVariance: 0.8, band: [0.38, 0.7], key: "Space" }],
    injections: { count: 3, amount: 0.22 },
    events: [{ drug: "isavuconazole", label: "An antifungal", kind: "sits", block: 0.6, start: [6, 10], length: [9, 12] }],
    tips: [],
    learned: "enzyme inhibition", reveal: "A blocked liver lets more of each pill through and clears it more slowly, so every dose hits twice.",
  },
  {
    world: 3, title: "Boost it on purpose", duration: 40, turnover: 0.03,
    tanks: [{ medicine: "nirmatrelvir", label: "COVID", drain: 2.0, dose: 0.4, gate: 0.5, band: [0.38, 0.7], key: "Space" }],
    boosters: { drug: "ritonavir", label: "Ritonavir", count: 3, effect: { kind: "breaks", block: 0.5, kill: 0.35, duration: 4 } },
    tips: [
      { when: "start", anchor: "liver", text: "The COVID pill drains almost at once" },
      { when: "time:3", anchor: "tokens", text: "Ritonavir disables the enzymes" },
    ],
    learned: "boosting", reveal: "Paxlovid pairs these two drugs because ritonavir blocks the liver enzyme that would clear the COVID drug.",
  },
  {
    world: 4, title: "Blind", duration: 38, bloodTests: 3, blind: true, turnover: 0.09,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: [0.38, 0.7], key: "Space" }],
    events: [{ drug: "rifampicin", label: "An antibiotic", kind: "induces", induce: 1.5, start: [5, 8], length: [12, 15] }],
    tips: [
      { when: "start", anchor: "tank", text: "You can't see the level anymore" },
      { when: "time:2.5", anchor: "tokens", text: "A blood test shows the level for 2 seconds" },
      { when: "event", anchor: "liver", text: "Watch the enzymes for clues" },
    ],
    learned: "enzyme induction", reveal: "The antibiotic made the liver build extra enzyme, which cleared medicine faster and lingered after the last dose.",
  },
  {
    world: 4, title: "Blind, and broken", duration: 36, bloodTests: 3, blind: true,
    tanks: [{ medicine: "metoprolol", label: "Blood pressure", drain: 0.3, dose: 0.3, band: [0.38, 0.7], key: "Space" }],
    events: [{ drug: "ritonavir", label: "An HIV medicine", kind: "breaks", block: 0.25, kill: 0.2, start: [6, 11], length: [8, 12] }],
    tips: [],
    learned: "time-dependent inhibition", reveal: "Some drugs destroy the enzyme instead of blocking it, so the drain stays slow until the liver builds more.",
  },
  {
    world: 5, title: "A week on antifungals", duration: 48,
    tanks: [
      { medicine: "isavuconazole", label: "Fungal infection", drain: 0.35, dose: 0.3, band: [0.38, 0.7], compete: 0.9, key: "Space" },
      { medicine: "simvastatin", label: "Cholesterol", drain: 0.45, dose: 0.36, band: [0.3, 0.72], auto: { period: 1.8, offset: 0.2 }, key: "Digit1" },
      { medicine: "felodipine", label: "Blood pressure", drain: 0.3, dose: 0.36, band: [0.3, 0.72], auto: { period: 2.4, offset: 0.9 }, key: "Digit2" },
      { medicine: "midazolam", label: "Sedative", drain: 0.18, dose: 0.3, band: [0.3, 0.72], auto: { period: 3.2, offset: 1.6 }, key: "Digit3" },
    ],
    tips: [
      { when: "start", anchor: "tank", text: "Tap the antifungal to dose it" },
      { when: "time:5", anchor: "tank:1", text: "Tap any other beaker to pause it" },
    ],
    learned: "managing interactions", reveal: "One way doctors handle an interaction is to pause a medicine for the length of a short course.",
  },
];


function mountDrain(root, host = {}) {
  const BOARD_W = 400;
  const BOARD_H = 560;
  const BASE_COPIES = 7;
  const MAX_COPIES = 14;
  const COPY_SIZE = 46;
  const PAPER = {
    ground: "#EDF1F0",
    grain: "rgba(26, 33, 36, 0.05)",
    ink: "#1A2124",
    inkSoft: "#5B686E",
    water: "#D4E6F1",
    waterLine: "#4F8DB8",
    frost: "#DDE3E6",
    band: "#3E9B6A",
    danger: "#FF6A1F",
    tissue: "#E0E8E5",
    capsule: "#7FB6DA",
    capsuleCap: "#FBFCFC",
  };
  const SPECIALS = [
    { id: "booster", key: "KeyR", shortcut: "R", has: (level) => Boolean(level.boosters), total: (level) => level.boosters.count, left: (state) => state.boostersLeft, name: (level) => level.boosters.label },
    { id: "injection", key: "KeyI", shortcut: "I", has: (level) => Boolean(level.injections), total: (level) => level.injections.count, left: (state) => state.injectionsLeft, name: () => "an injection" },
    { id: "test", key: "KeyB", shortcut: "B", has: (level) => Boolean(level.bloodTests), total: (level) => level.bloodTests, left: (state) => state.testsLeft, name: () => "a blood test" },
  ];
  const SHORTCUTS = { Space: "Space", Digit1: "1", Digit2: "2", Digit3: "3" };
  const TOKEN_GAP = 30;
  const calmMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const byId = (id) => root.querySelector(`#${id}`);
  const canvas = byId("board");
  const context = canvas.getContext("2d");
  const ui = {
    title: byId("level-title"),
    score: byId("score"),
    tip: byId("tip"),
    game: byId("game-view"),
    levels: byId("levels-view"),
    levelList: byId("level-list"),
    showLevels: byId("show-levels"),
    hits: byId("hits"),
    result: byId("result"),
    resultTitle: byId("result-title"),
    resultStars: byId("result-stars"),
    resultMeter: byId("result-meter"),
    resultFill: byId("result-fill"),
    resultValue: byId("result-value"),
    resultReveal: byId("result-reveal"),
    retry: byId("retry"),
    next: byId("next"),
    announcer: byId("announcer"),
  };

  const images = Object.fromEntries(Object.entries(SPRITES).map(([key, src]) => {
    const image = new Image();
    image.src = src;
    return [key, image];
  }));
  const grain = makeGrain();
  const slotOrder = [3, 2, 4, 1, 5, 0, 6, 10, 9, 11, 8, 12, 7, 13];

  let levelIndex = 0;
  let level = LEVELS[0];
  let world = WORLDS[0];
  let state = null;
  let view = null;
  let hits = { tanks: [], tray: null };
  let best = { ...loadBest(), ...(host.initialBest ?? {}) };
  let frameId = null;
  let resizeObserver = null;

  function loadBest() {
    try {
      return JSON.parse(localStorage.getItem("drain-best-v2") || "{}");
    } catch (error) {
      return {};
    }
  }

  function saveBest() {
    try {
      localStorage.setItem("drain-best-v2", JSON.stringify(best));
    } catch (error) {
      /* progress is a convenience */
    }
  }

  function makeGrain() {
    const grainCanvas = document.createElement("canvas");
    grainCanvas.width = BOARD_W * 2;
    grainCanvas.height = BOARD_H * 2;
    const grainContext = grainCanvas.getContext("2d");
    grainContext.fillStyle = PAPER.grain;
    for (let i = 0; i < 9000; i += 1) {
      grainContext.fillRect(Math.random() * grainCanvas.width, Math.random() * grainCanvas.height, 1.4, 1.4);
    }
    return grainCanvas;
  }

  function seededMolecules() {
    return Array.from({ length: 30 }, (_, index) => ({
      x: 0.08 + ((index * 0.6180339) % 1) * 0.84,
      depth: 0.08 + ((index * 0.7548776) % 1) * 0.84,
      phase: index * 1.7,
      tilt: ((index * 0.4142) % 1) * 6.28,
    }));
  }

  function newView() {
    return {
      phase: "ready",
      copies: [],
      particles: [],
      callouts: [],
      seenEvents: new Set(),
      pillX: new WeakMap(),
      landed: new WeakSet(),
      bitten: new WeakSet(),
      molecules: seededMolecules(),
      lastReading: null,
      shake: 0,
      flash: 0,
      wobble: level.tanks.map(() => 0),
      clock: 0,
    };
  }

  /* ---------- geometry ---------- */

  const TANK_LAYOUTS = {
    1: [[104, 296]],
    2: [[40, 180], [220, 360]],
    4: [[20, 124], [140, 206], [222, 288], [304, 370]],
  };

  function geometry() {
    const gated = Boolean(level.tanks[0].gate);
    const tankTop = gated ? 160 : (level.tanks.length > 1 ? 84 : 64);
    const tanks = TANK_LAYOUTS[level.tanks.length].map(([left, right]) => ({ left, right, top: tankTop, bottom: 398 }));
    return { gated, tanks, gateTop: 82, gateBottom: 134, liverTop: 432, liverBottom: 548 };
  }

  function levelToY(amount, tank) {
    return tank.bottom - amount * (tank.bottom - tank.top);
  }

  function tankCenter(tank) {
    return (tank.left + tank.right) / 2;
  }

  function slotPosition(slot, g) {
    const row = slot < 7 ? 0 : 1;
    const col = slot % 7;
    return { x: 56 + col * 48 + row * 24, y: g.liverTop + 38 + row * 50 };
  }

  function gateCopyPositions(g) {
    const y = (g.gateTop + g.gateBottom) / 2;
    return [150, 200, 250].map((x) => ({ x, y }));
  }

  function medicineImage(name) {
    return images[`${name}_med`] ?? images[name];
  }

  /* ---------- tap targets ---------- */

  function activeSpecial() {
    return SPECIALS.find((special) => special.has(level)) ?? null;
  }

  function trayRect() {
    const special = activeSpecial();
    if (!special) return null;
    return { x: 12, y: 12, width: 22 + special.total(level) * TOKEN_GAP, height: 40 };
  }

  function tankHitRect(tank) {
    return { x: tank.left - 10, y: tank.top - 40, width: tank.right - tank.left + 20, height: tank.bottom - tank.top + 50 };
  }

  function placeHit(button, rect) {
    button.style.left = `${(rect.x / BOARD_W) * 100}%`;
    button.style.top = `${(rect.y / BOARD_H) * 100}%`;
    button.style.width = `${(rect.width / BOARD_W) * 100}%`;
    button.style.height = `${(rect.height / BOARD_H) * 100}%`;
  }

  function makeHit(rect, shortcut, onActivate) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hit";
    button.setAttribute("aria-keyshortcuts", shortcut);
    placeHit(button, rect);
    button.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      onActivate();
    });
    button.addEventListener("click", (event) => {
      if (event.detail === 0) onActivate();
    });
    ui.hits.append(button);
    return button;
  }

  function buildHits() {
    ui.hits.innerHTML = "";
    const g = geometry();
    hits = { tanks: [], tray: null };
    level.tanks.forEach((spec, index) => {
      const activate = spec.auto ? () => togglePause(index) : () => takePill(index);
      hits.tanks[index] = makeHit(tankHitRect(g.tanks[index]), SHORTCUTS[spec.key], activate);
    });
    const special = activeSpecial();
    if (special) hits.tray = makeHit(trayRect(), special.shortcut, () => useSpecial(special.id));
  }

  function plainLabel(label) {
    return label === label.toUpperCase() ? label : label.charAt(0).toLowerCase() + label.slice(1);
  }

  function refreshHits() {
    const done = view.phase === "done";
    level.tanks.forEach((spec, index) => {
      const button = hits.tanks[index];
      const paused = state.tanks[index].paused;
      const action = spec.auto ? `${paused ? "Resume" : "Pause"} the ${plainLabel(spec.label)} medicine` : `Take a pill for ${plainLabel(spec.label)}`;
      button.setAttribute("aria-label", action);
      button.disabled = done;
    });
    const special = activeSpecial();
    if (!special) return;
    const left = special.left(state);
    hits.tray.setAttribute("aria-label", `Use ${special.name(level)}, ${left} left`);
    hits.tray.disabled = done || left <= 0;
  }

  /* ---------- actions ---------- */

  function begin() {
    if (view.phase === "ready") view.phase = "running";
  }

  function takePill(index) {
    if (view.phase === "done") return;
    if (Physics.takePill(state, level, index)) begin();
  }

  function togglePause(index) {
    if (view.phase === "done") return;
    Physics.togglePause(state, index);
    begin();
    refreshHits();
    announce(`${level.tanks[index].label} ${state.tanks[index].paused ? "paused" : "resumed"}.`);
  }

  const SPECIAL_ACTIONS = {
    booster: () => {
      if (!Physics.takeBooster(state, level)) return;
      view.callouts.push({ drug: level.boosters.drug, label: level.boosters.label, born: view.clock, fromButton: true });
      announce(`You took ${level.boosters.drug}.`);
    },
    injection: () => {
      if (!Physics.giveInjection(state, level)) return;
      injectParticles();
      announce("Injection given.");
    },
    test: () => {
      if (!Physics.takeBloodTest(state)) return;
      view.lastReading = { level: state.tanks[0].level, time: state.time };
      announce(`Blood test: ${describeReading(state.tanks[0].level)}.`);
    },
  };

  function useSpecial(id) {
    if (view.phase === "done") return;
    begin();
    SPECIAL_ACTIONS[id]();
    refreshHits();
  }

  function describeReading(amount) {
    const spec = level.tanks[0];
    if (amount > spec.band[1]) return "above the green band";
    if (amount < spec.band[0]) return "below the green band";
    return "inside the green band";
  }

  /* ---------- level flow ---------- */

  function loadLevel(index) {
    levelIndex = index;
    level = LEVELS[index];
    world = WORLDS[level.world];
    state = Physics.createState(level);
    view = newView();
    ui.title.textContent = level.title;
    ui.result.hidden = true;
    showGame();
    buildHits();
    refreshHits();
    updateScore();
    reconcileCopies(true);
    resetTips();
    snapshotState();
  }

  function finish() {
    view.phase = "done";
    refreshHits();
    const survived = state.outcome === "done";
    const percent = Physics.score(state, level);
    const stars = survived ? starCount(percent) : 0;
    best[levelIndex] = Math.max(best[levelIndex] ?? 0, stars);
    saveBest();
    host.onFinish?.({ level: levelIndex, stars: best[levelIndex], learned: survived ? level.learned : null });
    showResult(survived, percent, stars);
    if (!survived) {
      view.shake = calmMotion ? 0 : 14;
      view.flash = 1;
    }
  }

  function starCount(percent) {
    if (percent >= 0.88) return 3;
    if (percent >= 0.75) return 2;
    if (percent >= 0.55) return 1;
    return 0;
  }

  function starsMarkup(count) {
    return [0, 1, 2].map((i) => `<span class="${i < count ? "star on" : "star"}">${ICONS[i < count ? "star-fill" : "star"]}</span>`).join("");
  }

  function showResult(survived, percent, stars) {
    const titles = ["You made it, barely", "Good", "Steady hands", "Perfect rhythm"];
    const rounded = Math.round(percent * 100);
    ui.resultTitle.textContent = survived ? titles[stars] : "Overdose";
    ui.resultStars.innerHTML = starsMarkup(stars);
    ui.resultStars.setAttribute("aria-label", `${stars} of 3 stars`);
    ui.resultMeter.hidden = !survived;
    ui.resultMeter.setAttribute("aria-label", `In the green ${rounded}% of the time`);
    ui.resultFill.style.width = `${rounded}%`;
    ui.resultValue.textContent = `${rounded}%`;
    if (survived) ui.resultReveal.innerHTML = `You just learned about <strong>${level.learned}</strong>. ${level.reveal}`;
    else ui.resultReveal.textContent = `The ${plainLabel(level.tanks[state.overdosedTank ?? 0].label)} medicine passed the orange line at ${Math.round(state.time)} seconds.`;
    const isLast = levelIndex === LEVELS.length - 1;
    ui.next.querySelector(".label").textContent = isLast ? "Back to level 1" : "Next level";
    hideTip();
    ui.result.hidden = false;
    ui.next.focus({ preventScroll: true });
  }

  function updateScore() {
    ui.score.textContent = `${Math.round(Physics.score(state, level) * 100)}% in the green`;
  }

  function announce(message) {
    ui.announcer.textContent = message;
  }

  /* ---------- tips ---------- */

  const TIP_TRIGGERS = {
    start: () => true,
    time: (seconds) => view.phase === "running" && state.time >= Number(seconds),
    nearTop: () => state.tanks.some((tank, index) => tank.level > level.tanks[index].band[1] - 0.03),
    event: () => [...view.seenEvents].some((event) => !event.booster),
  };

  function resetTips() {
    view.tips = { shown: new Set(), current: null, shownAt: 0 };
    hideTip();
  }

  function tipIsDue(tip) {
    const [kind, value] = tip.when.split(":");
    return TIP_TRIGGERS[kind](value);
  }

  function tipIsOver(tip) {
    if (tip.until === "pill") return state.tanks.some((tank) => tank.lastPill > -Infinity);
    return view.clock - view.tips.shownAt > 3.2;
  }

  function tipAnchor(anchor) {
    const g = geometry();
    const [kind, index] = anchor.split(":");
    const tank = g.tanks[Number(index ?? 0)];
    const anchors = {
      tank: () => ({ x: tankCenter(tank), y: tank.top + 44, below: true }),
      liver: () => ({ x: 200, y: g.liverTop - 4, below: false }),
      gate: () => ({ x: 200, y: g.gateTop - 2, below: false }),
      tokens: () => {
        const tray = trayRect();
        return { x: tray.x + tray.width / 2, y: tray.y + tray.height + 8, below: true };
      },
    };
    return anchors[kind]();
  }

  function showTip(tip) {
    view.tips.current = tip;
    view.tips.shownAt = view.clock;
    view.tips.shown.add(tip);
    const anchor = tipAnchor(tip.anchor);
    ui.tip.textContent = tip.text;
    ui.tip.classList.toggle("tip--below", anchor.below);
    const scale = canvas.clientWidth / BOARD_W;
    const half = ui.tip.offsetWidth / 2 / scale;
    const x = Math.min(BOARD_W - half - 8, Math.max(half + 8, anchor.x));
    ui.tip.style.setProperty("--caret", `calc(50% + ${(anchor.x - x) * scale}px)`);
    ui.tip.style.left = `${(x / BOARD_W) * 100}%`;
    ui.tip.style.top = `${(anchor.y / BOARD_H) * 100}%`;
    ui.tip.dataset.visible = "true";
    if (tip.until === "pill") hits.tanks[0]?.classList.add("hit--nudge");
    announce(tip.text);
  }

  function hideTip() {
    ui.tip.dataset.visible = "false";
    if (view?.tips) view.tips.current = null;
    for (const button of hits.tanks) button?.classList.remove("hit--nudge");
  }

  function updateTips() {
    if (view.phase === "done") return;
    const current = view.tips.current;
    if (current) {
      if (tipIsOver(current)) hideTip();
      return;
    }
    const next = (level.tips ?? []).find((tip) => !view.tips.shown.has(tip) && tipIsDue(tip));
    if (next) showTip(next);
  }

  /* ---------- levels view ---------- */

  function showGame() {
    ui.game.hidden = false;
    ui.levels.hidden = true;
    ui.showLevels.setAttribute("aria-pressed", "false");
  }

  function showLevels() {
    renderLevelList();
    ui.game.hidden = true;
    ui.levels.hidden = false;
    ui.showLevels.setAttribute("aria-pressed", "true");
    ui.levelList.querySelector("button")?.focus({ preventScroll: true });
  }

  function renderLevelList() {
    ui.levelList.innerHTML = WORLDS.map((worldInfo, worldIndex) => {
      const buttons = LEVELS.map((entry, index) => ({ entry, index }))
        .filter(({ entry }) => entry.world === worldIndex)
        .map(({ entry, index }) => levelButton(entry, index))
        .join("");
      return `<li class="world">
        <img class="world-art" src="${SPRITES[worldInfo.enzyme]}" alt="${worldInfo.enzymeName} enzyme" width="56" height="56">
        <div class="world-body">
          <h2 class="world-name">${worldInfo.name}</h2>
          <p class="world-enzyme">${worldInfo.enzymeName}</p>
          <div class="world-levels">${buttons}</div>
        </div>
      </li>`;
    }).join("");
  }

  function levelButton(entry, index) {
    const stars = best[index] ?? 0;
    const current = index === levelIndex ? " current" : "";
    return `<button type="button" class="button button--stack level-button${current}" data-level="${index}" aria-label="${entry.title}, ${stars} of 3 stars">
      <span class="level-title">${entry.title}</span>
      <span class="level-stars" aria-hidden="true">${starsMarkup(stars)}</span>
    </button>`;
  }

  /* ---------- simulation-driven view state ---------- */

  function reconcileCopies(instant) {
    const target = Math.max(0, Math.min(MAX_COPIES, Math.round(state.enzyme * BASE_COPIES)));
    const alive = view.copies.filter((copy) => copy.dying === null);
    if (alive.length < target) addCopies(target - alive.length, instant);
    if (alive.length > target) retireCopies(alive, alive.length - target);
    view.copies = view.copies.filter((copy) => copy.dying === null || view.clock - copy.dying < 1.4);
  }

  function addCopies(count, instant) {
    const used = new Set(view.copies.filter((copy) => copy.dying === null).map((copy) => copy.slot));
    const free = slotOrder.filter((slot) => !used.has(slot));
    for (const slot of free.slice(0, count)) {
      view.copies.push({ slot, born: instant ? -10 : view.clock, dying: null, pulse: 0 });
    }
  }

  function retireCopies(alive, count) {
    const bySlot = [...alive].sort((a, b) => slotOrder.indexOf(b.slot) - slotOrder.indexOf(a.slot));
    for (const copy of bySlot.slice(0, count)) copy.dying = view.clock;
  }

  function jammingDrug() {
    const blocking = Physics.activeEvents(state).find((event) => (event.block ?? 0) > 0);
    if (blocking) return blocking.drug;
    const competitor = level.tanks.findIndex((spec, index) => spec.compete && state.tanks[index].level > 0.05);
    return competitor >= 0 ? level.tanks[competitor].medicine : null;
  }

  function trackArrivals() {
    for (const event of Physics.activeEvents(state)) {
      if (view.seenEvents.has(event)) continue;
      view.seenEvents.add(event);
      if (event.booster) continue;
      view.callouts.push({ drug: event.drug, label: event.label, born: view.clock, fromButton: false });
      announce(`Your patient started ${plainLabel(event.label ?? event.drug)}.`);
    }
  }

  function trackPills(g) {
    level.tanks.forEach((spec, index) => {
      const tank = g.tanks[index];
      for (const pill of state.tanks[index].pills) {
        if (!view.pillX.has(pill)) view.pillX.set(pill, tankCenter(tank) + (Math.random() - 0.5) * (tank.right - tank.left) * 0.45);
        const landing = Physics.landingTime(spec);
        if (g.gated && pill.age >= landing * 0.45 && !view.bitten.has(pill)) biteAtGate(pill, g);
        if (pill.age >= landing && !view.landed.has(pill)) landPill(pill, index, tank);
      }
    });
  }

  function biteAtGate(pill, g) {
    view.bitten.add(pill);
    const x = view.pillX.get(pill);
    for (const target of gateCopyPositions(g)) {
      view.particles.push({ kind: "crumb", x, y: (g.gateTop + g.gateBottom) / 2, tx: target.x, ty: target.y, born: view.clock, life: 0.45 });
    }
  }

  function landPill(pill, index, tank) {
    view.landed.add(pill);
    view.wobble[index] = Math.min(2, view.wobble[index] + 1);
    if (!Physics.isRevealed(state, level)) return;
    const x = view.pillX.get(pill);
    const y = levelToY(state.tanks[index].level, tank);
    for (let i = 0; i < 9; i += 1) {
      view.particles.push({ kind: "splash", x, y, vx: (Math.random() - 0.5) * 170, vy: -110 - Math.random() * 140, born: view.clock, life: 0.55 });
    }
  }

  function injectParticles() {
    const tank = geometry().tanks[0];
    for (let i = 0; i < 14; i += 1) {
      const x = tankCenter(tank) + (Math.random() - 0.5) * 40;
      view.particles.push({ kind: "splash", x, y: tank.top - 10, vx: (Math.random() - 0.5) * 30, vy: 180 + Math.random() * 120, born: view.clock + i * 0.02, life: 0.5 });
    }
  }

  function emitDrain(dt, g) {
    const alive = view.copies.filter((copy) => copy.dying === null);
    if (!alive.length) return;
    level.tanks.forEach((spec, index) => {
      const flow = spec.drain * Physics.capacity(state) * state.tanks[index].level;
      if (Math.random() > flow * dt * 45) return;
      const target = alive[Math.floor(Math.random() * alive.length)];
      const to = slotPosition(target.slot, g);
      view.particles.push({ kind: "drop", x: tankCenter(g.tanks[index]), y: g.liverTop - 4, tx: to.x, ty: to.y, born: view.clock, life: 0.7, target });
    });
  }

  function ageParticles(dt) {
    for (const particle of view.particles) {
      if (particle.kind !== "splash") continue;
      particle.vy += 650 * dt;
      particle.x += particle.vx * dt;
      particle.y += particle.vy * dt;
    }
    for (const particle of view.particles) {
      if (particle.kind === "drop" && view.clock - particle.born >= particle.life) particle.target.pulse = 1;
    }
    view.particles = view.particles.filter((particle) => view.clock - particle.born < particle.life);
  }

  function update(dt) {
    view.clock += dt;
    view.wobble = view.wobble.map((value) => value * Math.exp(-dt * 2.2));
    view.shake *= Math.exp(-dt * 8);
    view.flash *= Math.exp(-dt * 2.5);
    for (const copy of view.copies) copy.pulse *= Math.exp(-dt * 6);
    ageParticles(dt);
    updateTips();
    if (view.phase !== "running") return;
    const g = geometry();
    Physics.step(state, level, dt);
    trackArrivals();
    trackPills(g);
    reconcileCopies(false);
    emitDrain(dt, g);
    updateScore();
    refreshHits();
    if (state.outcome) finish();
  }

  /* ---------- drawing ---------- */

  function drawBackground() {
    context.fillStyle = PAPER.ground;
    context.fillRect(0, 0, BOARD_W, BOARD_H);
    context.drawImage(grain, 0, 0, BOARD_W, BOARD_H);
  }

  function drawTissue(top, bottom) {
    context.fillStyle = PAPER.tissue;
    context.beginPath();
    context.moveTo(0, bottom);
    context.lineTo(0, top + 6);
    for (let x = 0; x <= BOARD_W; x += 10) context.lineTo(x, top + Math.sin(x * 0.05) * 4);
    context.lineTo(BOARD_W, bottom);
    context.closePath();
    context.fill();
  }

  function surfaceY(x, index, tank) {
    const base = levelToY(state.tanks[index].level, tank);
    const amplitude = (calmMotion ? 0.3 : 1) * (0.8 + view.wobble[index] * 4);
    const t = view.clock;
    return base + Math.sin(x * 0.045 + t * 3.1 + index) * amplitude + Math.sin(x * 0.11 - t * 2.2) * amplitude * 0.5;
  }

  function traceSurface(index, tank, continuePath) {
    for (let x = tank.left; x <= tank.right; x += 4) {
      const y = surfaceY(x, index, tank);
      if (x === tank.left && !continuePath) context.moveTo(x, y);
      else context.lineTo(x, y);
    }
  }

  function drawBand(spec, tank) {
    const top = levelToY(spec.band[1], tank);
    const bottom = levelToY(spec.band[0], tank);
    context.save();
    context.globalAlpha = 0.14;
    context.fillStyle = PAPER.band;
    context.fillRect(tank.left, top, tank.right - tank.left, bottom - top);
    context.globalAlpha = 1;
    context.strokeStyle = PAPER.band;
    context.lineWidth = 2;
    context.setLineDash([6, 6]);
    for (const y of [top, bottom]) {
      context.beginPath();
      context.moveTo(tank.left, y);
      context.lineTo(tank.right, y);
      context.stroke();
    }
    context.restore();
  }

  function drawWater(spec, index, tank) {
    const amount = state.tanks[index].level;
    if (amount <= 0.003) return;
    context.save();
    context.beginPath();
    context.moveTo(tank.left, tank.bottom);
    traceSurface(index, tank, true);
    context.lineTo(tank.right, tank.bottom);
    context.closePath();
    context.fillStyle = PAPER.water;
    context.globalAlpha = 0.9;
    context.fill();
    context.clip();
    context.globalAlpha = 1;
    drawDissolvedMolecules(spec, amount, tank);
    context.restore();
    context.save();
    context.strokeStyle = PAPER.waterLine;
    context.lineWidth = 2.5;
    context.beginPath();
    traceSurface(index, tank);
    context.stroke();
    context.restore();
  }

  function drawDissolvedMolecules(spec, amount, tank) {
    const image = medicineImage(spec.medicine);
    const width = tank.right - tank.left;
    const available = Math.round(view.molecules.length * Math.min(1, width / 192));
    const shown = Math.round((amount / Physics.OVERDOSE) * available);
    const depth = tank.bottom - levelToY(amount, tank);
    for (const molecule of view.molecules.slice(0, shown)) {
      const bob = calmMotion ? 0 : Math.sin(view.clock * 0.9 + molecule.phase) * 3;
      const x = tank.left + molecule.x * width;
      const y = tank.bottom - molecule.depth * depth + bob;
      drawSprite(image, x, y, 20, molecule.tilt + (calmMotion ? 0 : view.clock * 0.15), 0.9);
    }
  }

  function drawFrost(tank) {
    context.save();
    context.fillStyle = PAPER.frost;
    context.fillRect(tank.left, tank.top, tank.right - tank.left, tank.bottom - tank.top);
    context.globalAlpha = 0.5;
    context.drawImage(grain, tank.left * 2, tank.top * 2, (tank.right - tank.left) * 2, (tank.bottom - tank.top) * 2, tank.left, tank.top, tank.right - tank.left, tank.bottom - tank.top);
    context.restore();
  }

  function drawLastReading(tank) {
    if (!view.lastReading) return;
    const y = levelToY(view.lastReading.level, tank);
    const ago = Math.round(state.time - view.lastReading.time);
    context.save();
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 2;
    context.setLineDash([3, 4]);
    context.beginPath();
    context.moveTo(tank.left, y);
    context.lineTo(tank.right, y);
    context.stroke();
    context.fillStyle = PAPER.ink;
    context.font = '600 13px "Atkinson Hyperlegible Next", system-ui, sans-serif';
    context.textAlign = "left";
    context.fillText(`${ago}s ago`, tank.right + 6, y + 4);
    context.restore();
  }

  function drawTestTimer(tank) {
    const remaining = state.revealUntil - state.time;
    if (!level.blind || remaining <= 0 || state.outcome) return;
    const fraction = remaining / Physics.TEST_DURATION;
    context.save();
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 3;
    context.beginPath();
    context.arc(tank.right - 18, tank.top + 18, 10, -Math.PI / 2, -Math.PI / 2 + fraction * Math.PI * 2);
    context.stroke();
    context.restore();
  }

  function drawSprite(image, x, y, height, rotation, alpha) {
    if (!image?.complete || !image.naturalHeight) return;
    const width = height * (image.naturalWidth / image.naturalHeight);
    context.save();
    context.globalAlpha = alpha;
    context.translate(x, y);
    context.rotate(rotation);
    context.drawImage(image, -width / 2, -height / 2, width, height);
    context.restore();
  }

  function drawGraduations(tank) {
    context.strokeStyle = PAPER.inkSoft;
    context.lineWidth = 1.5;
    for (let mark = 1; mark <= 9; mark += 1) {
      const y = levelToY(mark / 10, tank);
      context.beginPath();
      context.moveTo(tank.left, y);
      context.lineTo(tank.left + (mark === 5 ? 14 : 8), y);
      context.stroke();
    }
  }

  function drawOverdoseLine(spec, index, tank) {
    const y = levelToY(Physics.OVERDOSE, tank);
    const visible = Physics.isRevealed(state, level);
    const amount = visible ? state.tanks[index].level : 0;
    const closeness = Math.max(0, (amount - spec.band[1]) / (Physics.OVERDOSE - spec.band[1]));
    const pulse = calmMotion ? 1 : 0.65 + 0.35 * Math.sin(view.clock * 11);
    context.save();
    context.strokeStyle = PAPER.danger;
    context.lineWidth = 2.5;
    context.shadowColor = PAPER.danger;
    context.shadowBlur = 4 + 26 * closeness * pulse;
    context.beginPath();
    context.moveTo(tank.left, y);
    context.lineTo(tank.right, y);
    context.stroke();
    context.restore();
  }

  function drawBeaker(tank) {
    context.save();
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 3;
    context.lineJoin = "round";
    context.beginPath();
    context.moveTo(tank.left - 8, tank.top);
    context.lineTo(tank.left, tank.top);
    context.lineTo(tank.left, tank.bottom);
    context.lineTo(tank.right, tank.bottom);
    context.lineTo(tank.right, tank.top);
    context.lineTo(tank.right + 8, tank.top);
    context.stroke();
    context.restore();
  }

  function wrapLabel(text, maxWidth) {
    const lines = [];
    for (const word of text.split(" ")) {
      const last = lines[lines.length - 1];
      if (last && context.measureText(`${last} ${word}`).width <= maxWidth) lines[lines.length - 1] = `${last} ${word}`;
      else lines.push(word);
    }
    return lines;
  }

  function drawTankLabel(spec, index, tank) {
    const paused = state.tanks[index].paused;
    context.save();
    context.fillStyle = paused ? PAPER.inkSoft : PAPER.ink;
    context.font = `600 ${level.tanks.length > 2 ? 12 : 14}px "Atkinson Hyperlegible Next", system-ui, sans-serif`;
    context.textAlign = "center";
    const lines = wrapLabel(spec.label, tank.right - tank.left + 16);
    lines.forEach((line, lineIndex) => {
      context.fillText(line, tankCenter(tank), tank.top - 12 - (lines.length - 1 - lineIndex) * 14);
    });
    context.restore();
  }

  function drawPauseBadge(spec, index, tank) {
    if (!spec.auto) return;
    const paused = state.tanks[index].paused;
    const x = tankCenter(tank);
    const y = tank.top + 22;
    context.save();
    if (paused) {
      context.globalAlpha = 0.5;
      context.fillStyle = PAPER.ground;
      context.fillRect(tank.left, tank.top, tank.right - tank.left, tank.bottom - tank.top);
      context.globalAlpha = 1;
    }
    context.fillStyle = paused ? PAPER.ink : "#FFFFFF";
    context.beginPath();
    context.arc(x, y, 13, 0, Math.PI * 2);
    context.fill();
    context.fillStyle = paused ? "#FFFFFF" : PAPER.ink;
    if (paused) {
      context.beginPath();
      context.moveTo(x - 4, y - 6);
      context.lineTo(x + 6, y);
      context.lineTo(x - 4, y + 6);
      context.closePath();
      context.fill();
    } else {
      context.fillRect(x - 5, y - 6, 3.5, 12);
      context.fillRect(x + 1.5, y - 6, 3.5, 12);
    }
    context.restore();
  }

  function drawPipe(tank, g) {
    const x = tankCenter(tank);
    context.save();
    context.fillStyle = PAPER.water;
    context.fillRect(x - 6, tank.bottom, 12, g.liverTop - tank.bottom + 2);
    context.strokeStyle = PAPER.ink;
    context.lineWidth = 3;
    context.beginPath();
    context.moveTo(x - 6, tank.bottom);
    context.lineTo(x - 6, g.liverTop + 2);
    context.moveTo(x + 6, tank.bottom);
    context.lineTo(x + 6, g.liverTop + 2);
    context.stroke();
    context.restore();
  }

  function drawTank(spec, index, tank, g) {
    drawPipe(tank, g);
    if (Physics.isRevealed(state, level)) drawWater(spec, index, tank);
    else drawFrost(tank);
    drawBand(spec, tank);
    if (!Physics.isRevealed(state, level)) drawLastReading(tank);
    drawGraduations(tank);
    drawOverdoseLine(spec, index, tank);
    drawPauseBadge(spec, index, tank);
    drawBeaker(tank);
    drawTankLabel(spec, index, tank);
    drawTestTimer(tank);
  }

  function copyScale(copy) {
    if (calmMotion) return 1;
    const age = view.clock - copy.born;
    const pop = age < 0.5 ? 1 + Math.sin(Math.min(1, age / 0.5) * Math.PI) * 0.25 - (1 - Math.min(1, age / 0.25)) : 1;
    return Math.max(0, pop) * (1 + copy.pulse * 0.08);
  }

  function drawCopy(copy, position, jammedBy) {
    const bob = calmMotion ? 0 : Math.sin(view.clock * 1.3 + copy.slot) * 1.5;
    if (copy.dying !== null) {
      const fade = Math.min(1, (view.clock - copy.dying) / 1.4);
      drawSprite(images[`${world.enzyme}_dead`], position.x, position.y + fade * 16, COPY_SIZE, 0, 1 - fade);
      return;
    }
    drawSprite(images[world.enzyme], position.x, position.y + bob, COPY_SIZE * copyScale(copy), 0, 1);
    if (jammedBy) drawSprite(images[jammedBy], position.x, position.y + bob, 17, 0.4, 1);
  }

  function drawLiver(g) {
    drawTissue(g.liverTop, g.liverBottom + 12);
    const drug = jammingDrug();
    const alive = view.copies.filter((copy) => copy.dying === null).sort((a, b) => slotOrder.indexOf(a.slot) - slotOrder.indexOf(b.slot));
    const jammedCount = drug ? Math.round(state.block * alive.length) : 0;
    const jammed = new Set(alive.slice(0, jammedCount));
    for (const copy of view.copies) drawCopy(copy, slotPosition(copy.slot, g), jammed.has(copy) ? drug : null);
  }

  function drawGate(g) {
    if (!g.gated) return;
    context.fillStyle = PAPER.tissue;
    context.fillRect(0, g.gateTop, BOARD_W, g.gateBottom - g.gateTop);
    const drug = jammingDrug();
    for (const position of gateCopyPositions(g)) {
      drawSprite(images[world.enzyme], position.x, position.y, 40, 0, Math.min(1, 0.35 + Physics.capacity(state) * 0.65));
      if (drug && state.block > 0.3) drawSprite(images[drug], position.x, position.y, 15, 0.4, 1);
    }
  }

  const iconPathCache = {};
  function iconPaths(name) {
    iconPathCache[name] ??= [...ICONS[name].matchAll(/ d="([^"]+)"/g)].map((match) => new Path2D(match[1]));
    return iconPathCache[name];
  }

  function drawIcon(name, x, y, size, color, alpha) {
    context.save();
    context.globalAlpha = alpha;
    context.translate(x - size / 2, y - size / 2);
    context.scale(size / 256, size / 256);
    context.fillStyle = color;
    for (const path of iconPaths(name)) context.fill(path);
    context.restore();
  }

  const TOKEN_ART = {
    booster: (x, y, alpha) => drawCapsule(x, y, 0.8, alpha, "#EFC94C"),
    injection: (x, y, alpha) => drawIcon("syringe", x, y, 24, PAPER.ink, alpha),
    test: (x, y, alpha) => drawIcon("drop", x, y, 24, "#B8483E", alpha),
  };

  function drawTray() {
    const special = activeSpecial();
    if (!special) return;
    const rect = trayRect();
    const left = special.left(state);
    context.save();
    context.fillStyle = "rgba(255, 255, 255, 0.85)";
    context.beginPath();
    context.roundRect(rect.x, rect.y, rect.width, rect.height, rect.height / 2);
    context.fill();
    context.restore();
    for (let i = 0; i < special.total(level); i += 1) {
      TOKEN_ART[special.id](rect.x + 26 + i * TOKEN_GAP, rect.y + rect.height / 2, i < left ? 1 : 0.2);
    }
  }

  function drawCapsule(x, y, scale, alpha, cap = PAPER.capsule) {
    context.save();
    context.globalAlpha = alpha;
    context.translate(x, y);
    context.scale(scale, scale);
    context.rotate(-0.35);
    context.lineWidth = 2.5;
    context.strokeStyle = PAPER.ink;
    context.fillStyle = PAPER.capsuleCap;
    context.beginPath();
    context.roundRect(-14, -6.5, 28, 13, 6.5);
    context.fill();
    context.fillStyle = cap;
    context.beginPath();
    context.roundRect(0, -6.5, 14, 13, [0, 6.5, 6.5, 0]);
    context.fill();
    context.beginPath();
    context.roundRect(-14, -6.5, 28, 13, 6.5);
    context.stroke();
    context.restore();
  }

  function drawPills(g) {
    const revealed = Physics.isRevealed(state, level);
    level.tanks.forEach((spec, index) => {
      const tank = g.tanks[index];
      const landing = Physics.landingTime(spec);
      const surface = revealed ? levelToY(state.tanks[index].level, tank) : tank.top + 24;
      const scale = level.tanks.length > 2 ? 0.75 : 1;
      for (const pill of state.tanks[index].pills) {
        const x = view.pillX.get(pill) ?? tankCenter(tank);
        const bite = view.bitten.has(pill) ? 0.55 + 0.45 * Physics.throughGate(state, spec, pill.variance) : 1;
        if (pill.age < landing) {
          const progress = pill.age / landing;
          drawCapsule(x, 12 + (surface - 12) * progress * progress, scale * bite, 1);
        } else if (revealed) {
          const dissolved = 1 - pill.remaining / spec.dose;
          drawCapsule(x, surface + 10 + dissolved * 22, scale * bite, Math.max(0, 1 - dissolved));
        }
      }
    });
  }

  function drawParticles() {
    for (const particle of view.particles) {
      const age = (view.clock - particle.born) / particle.life;
      if (age < 0) continue;
      context.save();
      if (particle.kind === "splash") {
        context.globalAlpha = 1 - age;
        context.fillStyle = PAPER.waterLine;
        context.beginPath();
        context.arc(particle.x, particle.y, 2.4, 0, Math.PI * 2);
        context.fill();
      } else {
        const x = particle.x + (particle.tx - particle.x) * age;
        const y = particle.y + (particle.ty - particle.y) * age - Math.sin(age * Math.PI) * 18;
        context.globalAlpha = particle.kind === "crumb" ? 1 - age * 0.6 : 1;
        context.fillStyle = particle.kind === "crumb" ? PAPER.capsule : PAPER.waterLine;
        context.beginPath();
        context.arc(x, y, particle.kind === "crumb" ? 3 : 2.6, 0, Math.PI * 2);
        context.fill();
      }
      context.restore();
    }
  }

  function drawCallouts(g) {
    const anchorY = g.tanks[0].top + 70;
    for (const callout of view.callouts) {
      const age = view.clock - callout.born;
      if (age > 3) continue;
      const settle = Math.min(1, age / 0.35);
      const leave = Math.max(0, (age - 2.3) / 0.7);
      const startX = callout.fromButton ? 350 : 52;
      const x = startX + (200 - startX) * leave;
      const y = anchorY + (g.liverTop + 40 - anchorY) * leave * leave;
      const alpha = settle * (1 - leave * 0.8);
      drawSprite(images[callout.drug], x, y, 58 * (1 - leave * 0.6), 0.3, alpha);
      context.save();
      context.globalAlpha = alpha * (1 - leave);
      context.fillStyle = PAPER.ink;
      context.font = '600 15px "Atkinson Hyperlegible Next", system-ui, sans-serif';
      context.textAlign = "center";
      context.fillText(callout.label ?? callout.drug, x, y + 46);
      context.restore();
    }
  }

  function drawTimer() {
    const progress = Math.min(1, state.time / level.duration);
    context.fillStyle = "rgba(26, 33, 36, 0.12)";
    context.fillRect(24, 552, BOARD_W - 48, 4);
    context.fillStyle = PAPER.ink;
    context.fillRect(24, 552, (BOARD_W - 48) * progress, 4);
  }

  function drawFlash() {
    if (view.flash < 0.02) return;
    context.save();
    context.globalAlpha = view.flash * 0.22;
    context.fillStyle = PAPER.danger;
    context.fillRect(0, 0, BOARD_W, BOARD_H);
    context.restore();
  }

  function draw() {
    const g = geometry();
    context.save();
    context.clearRect(0, 0, BOARD_W, BOARD_H);
    if (view.shake > 0.3) context.translate((Math.random() - 0.5) * view.shake, (Math.random() - 0.5) * view.shake);
    drawBackground();
    drawGate(g);
    level.tanks.forEach((spec, index) => drawTank(spec, index, g.tanks[index], g));
    drawLiver(g);
    drawPills(g);
    drawParticles();
    drawCallouts(g);
    drawTray();
    drawTimer();
    drawFlash();
    context.restore();
  }

  /* ---------- plumbing ---------- */

  function resize() {
    const ratio = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth;
    canvas.width = Math.round(cssWidth * ratio);
    canvas.height = Math.round(cssWidth * (BOARD_H / BOARD_W) * ratio);
    const scale = (cssWidth / BOARD_W) * ratio;
    context.setTransform(scale, 0, 0, scale, 0, 0);
  }

  let lastFrame = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - lastFrame) / 1000);
    lastFrame = now;
    update(dt);
    draw();
    frameId = requestAnimationFrame(frame);
  }

  function onKey(event) {
    if (!ui.levels.hidden || event.repeat) return;
    if (event.target instanceof HTMLButtonElement && event.target.closest(".result, .hit")) return;
    const tankIndex = level.tanks.findIndex((spec) => spec.key === event.code);
    const special = SPECIALS.find((entry) => entry.key === event.code && entry.has(level));
    if (tankIndex < 0 && !special) return;
    event.preventDefault();
    if (special) useSpecial(special.id);
    else if (level.tanks[tankIndex].auto) togglePause(tankIndex);
    else takePill(tankIndex);
  }

  function snapshotState() {
    host.onLevel?.(levelIndex);
  }

  function bindControls() {
    ui.retry.addEventListener("click", () => loadLevel(levelIndex));
    ui.next.addEventListener("click", () => loadLevel((levelIndex + 1) % LEVELS.length));
    ui.showLevels.addEventListener("click", () => (ui.levels.hidden ? showLevels() : showGame()));
    ui.levelList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-level]");
      if (button) loadLevel(Number(button.dataset.level));
    });
    root.addEventListener("keydown", onKey);
    root.addEventListener("pointerdown", () => root.focus({ preventScroll: true }), true);
  }

  function fillIcons() {
    for (const holder of root.querySelectorAll("[data-icon]")) holder.innerHTML = ICONS[holder.dataset.icon];
  }

  function start(data) {
    fillIcons();
    resize();
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);
    bindControls();
    loadLevel(Math.min(LEVELS.length - 1, Math.max(0, data?.levelIndex ?? 0)));
    frameId = requestAnimationFrame(frame);
  }

  function stop() {
    cancelAnimationFrame(frameId);
    resizeObserver?.disconnect();
  }

  start(host.startData ?? {});
  return stop;
}


function ensureFont() {
  if (document.querySelector("link[data-drain-font]")) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = FONT_URL;
  link.dataset.drainFont = "";
  document.head.append(link);
}

function recordFinish(model, { level, stars, learned }) {
  const progress = { ...(model.get("progress") ?? {}) };
  progress[String(level)] = stars;
  model.set("progress", progress);
  if (learned) model.set("learned", learned);
  model.save_changes();
}

export default {
  render({ model, el }) {
    ensureFont();
    const root = document.createElement("div");
    root.className = "drain";
    root.tabIndex = -1;
    root.innerHTML = `<style>${CSS}</style>${MARKUP}`;
    el.append(root);
    return mountDrain(root, {
      initialBest: model.get("progress") ?? {},
      onFinish: (result) => recordFinish(model, result),
    });
  },
};
