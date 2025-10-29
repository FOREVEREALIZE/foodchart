import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export function renderTimedLines(lineG, timedData, x, y) {
    const lineGen = d3.line()
        .x(d => x(d.percent))
        .y(d => y(d.fixed));

    const lineData = timedData.map(v => {
        const steps = v.healing.steps.toSorted((a, b) => a.tick - b.tick);
        return [v.healing.base, ...steps];
    });

    lineG.selectAll('path.connection-line')
        .data(lineData)
        .join('path')
        .attr('class', 'connection-line')
        .attr('fill', 'none')
        .attr('stroke', 'red')
        .attr('stroke-width', 2)
        .attr('opacity', 0.05)
        .attr('d', d => lineGen(d));
}