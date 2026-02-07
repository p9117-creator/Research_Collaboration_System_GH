import typer
import sys
import os
from rich.console import Console
from rich.table import Table
from typing import Optional

# Add code directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import ResearchDatabaseManager, load_database_config
from query_engine import ResearchQueryEngine

app = typer.Typer(help="Research Collaboration System CLI")
console = Console()

# Global state
state = {"db": None, "qe": None}

def get_db():
    if state["db"] is None:
        config = load_database_config()
        state["db"] = ResearchDatabaseManager(config)
        state["db"].connect_all()
        state["qe"] = ResearchQueryEngine(state["db"])
    return state["db"], state["qe"]

@app.command()
def info():
    """Show system information and database status"""
    db, _ = get_db()
    
    table = Table(title="Database Status")
    table.add_column("Database", style="cyan")
    table.add_column("Status", style="green")
    
    # Check MongoDB
    try:
        db.mongodb.client.admin.command('ping')
        table.add_row("MongoDB", "Connected")
    except:
        table.add_row("MongoDB", "Disconnected", style="red")

    # Check Neo4j
    try:
        with db.neo4j.driver.session() as session:
            session.run("RETURN 1")
        table.add_row("Neo4j", "Connected")
    except:
        table.add_row("Neo4j", "Disconnected", style="red")

    # Check Redis
    try:
        db.redis.client.ping()
        table.add_row("Redis", "Connected")
    except:
        table.add_row("Redis", "Disconnected", style="red")

    # Check Cassandra
    try:
        db.cassandra.session.execute("SELECT 1")
        table.add_row("Cassandra", "Connected")
    except:
        table.add_row("Cassandra", "Disconnected", style="red")

    console.print(table)

@app.command()
def list_researchers(department: Optional[str] = None, limit: int = 20):
    """List researchers with optional department filter"""
    _, qe = get_db()
    
    query = {}
    if department:
        query["academic_profile.department_id"] = department
        
    researchers = qe.db_manager.mongodb.search_researchers(query, limit=limit)
    
    table = Table(title=f"Researchers {'(' + department + ')' if department else ''}")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Department")
    table.add_column("Position")
    
    for r in researchers:
        start_info = r.get("personal_info", {})
        academic = r.get("academic_profile", {})
        
        name = f"{start_info.get('first_name', '')} {start_info.get('last_name', '')}"
        table.add_row(
            str(r.get("_id")),
            name,
            academic.get("department_id", "N/A"),
            academic.get("position", "N/A")
        )
        
    console.print(table)
    console.print(f"Total found: {len(researchers)}")

@app.command()
def list_projects(status: Optional[str] = None, limit: int = 20):
    """List projects with optional status filter"""
    _, qe = get_db()
    
    query = {}
    if status:
        query["status"] = status
        
    projects = qe.db_manager.mongodb.search_projects(query, limit=limit)
    
    table = Table(title=f"Projects {'(' + status + ')' if status else ''}")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Status")
    table.add_column("Funding")
    
    for p in projects:
        funding = p.get("funding", {}).get("amount", 0)
        table.add_row(
            str(p.get("_id")),
            p.get("title", "N/A"),
            p.get("status", "N/A"),
            f"${funding:,.2f}"
        )
        
    console.print(table)
    console.print(f"Total found: {len(projects)}")

@app.command()
def analytics(department_id: str):
    """Show analytics for a department"""
    _, qe = get_db()
    
    with console.status(f"[bold green]Calculating analytics for {department_id}..."):
        data = qe.get_department_analytics(department_id)
        
    if "error" in data:
        console.print(f"[bold red]Error:[/bold red] {data['error']}")
        return

    console.print(f"\n[bold underline]Analytics for {department_id}[/bold underline]\n")
    
    # Overview
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column(justify="right")
    grid.add_row("Total Researchers:", str(data.get("researcher_count", 0)))
    grid.add_row("Total Publications:", str(data.get("total_publications", 0)))
    grid.add_row("Average H-Index:", f"{data.get('avg_h_index', 0):.2f}")
    
    console.print(grid)
    
    # Top Researchers
    if "top_researchers" in data:
        table = Table(title="Top Researchers")
        table.add_column("Name")
        table.add_column("H-Index", justify="right")
        
        for r in data["top_researchers"]:
            table.add_row(r.get("name"), str(r.get("h_index")))
            
        console.print(table)

if __name__ == "__main__":
    app()
