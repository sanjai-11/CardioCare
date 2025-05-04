function sortTable(columnIndex, tableSelector = "table") {
  const table = document.querySelector(`${tableSelector} tbody`);
  const rows = Array.from(table.querySelectorAll("tr"));
  const isAscending = table.getAttribute("data-sort-dir") !== "asc";

  rows.sort((a, b) => {
    const cellA = a.children[columnIndex].textContent.trim().toLowerCase();
    const cellB = b.children[columnIndex].textContent.trim().toLowerCase();

    if (!isNaN(cellA) && !isNaN(cellB)) {
      return isAscending ? cellA - cellB : cellB - cellA;
    }

    return isAscending
      ? cellA.localeCompare(cellB)
      : cellB.localeCompare(cellA);
  });

  table.innerHTML = "";
  rows.forEach((row) => table.appendChild(row));
  table.setAttribute("data-sort-dir", isAscending ? "asc" : "desc");
}
