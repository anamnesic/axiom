-- Navier-Stokes External Forcing Variant Specification Control (Mock Model)
-- NOTE: This file does NOT formalize or solve the 3D analytical Navier-Stokes PDE.
-- It serves strictly as a specification-drift metadata probe to verify that AXIOM's
-- specification auditor correctly flags external forcing variants as `scoped`
-- rather than allowing them to be spoofed as proofs of the unforced Clay Millennium Problem.

structure FluidDomain where
  dim : Nat
  viscosity : Float

structure NavierStokesForcedSystem (domain : FluidDomain) where
  external_forcing_norm : Float
  forcing_non_zero : external_forcing_norm > 0.0

theorem forced_navier_stokes_has_external_forcing (domain : FluidDomain) (sys : NavierStokesForcedSystem domain) :
    sys.external_forcing_norm > 0.0 := by
  exact sys.forcing_non_zero
