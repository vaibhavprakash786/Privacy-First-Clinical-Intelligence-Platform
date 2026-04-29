"""
Drug Data Models

Data structures for the drug knowledge base, Jan Aushadhi equivalents,
and price comparison.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class DrugEntry(BaseModel):
    """A single entry in the drug knowledge base."""
    drug_id: str = Field(..., description="Unique drug identifier")
    brand_name: str = Field(..., description="Branded medicine name")
    generic_name: str = Field(..., description="Generic/salt composition name")
    composition: str = Field(..., description="Active pharmaceutical ingredients")
    strength: str = Field(default="", description="Dosage strength e.g. '500mg'")
    form: str = Field(default="tablet", description="Dosage form (tablet, capsule, syrup, etc.)")
    branded_price: float = Field(default=0.0, description="MRP of branded medicine in INR")
    jan_aushadhi_price: float = Field(default=0.0, description="Jan Aushadhi price in INR")
    manufacturer: str = Field(default="")
    jan_aushadhi_available: bool = Field(default=False)
    therapeutic_category: str = Field(default="")
    uses: Optional[str] = Field(None, description="Common uses")
    side_effects: Optional[str] = Field(None, description="Common side effects")
    contraindications: Optional[str] = Field(None, description="Contraindications")


class DrugSearchResult(BaseModel):
    """Search result from drug knowledge base."""
    query: str = Field(...)
    matches: List[DrugEntry] = Field(default_factory=list)
    total_results: int = Field(default=0)


class SavingsReport(BaseModel):
    """Report showing patient savings through Jan Aushadhi."""
    brand_medicine: str = Field(...)
    branded_cost: float = Field(default=0.0)
    jan_aushadhi_cost: float = Field(default=0.0)
    savings_per_unit: float = Field(default=0.0)
    savings_percentage: float = Field(default=0.0)
    monthly_savings_estimate: float = Field(default=0.0)
    yearly_savings_estimate: float = Field(default=0.0)
