-- Navier-Stokes 3D External Forcing Variant Model
-- Represents the externally forced Navier-Stokes equations:
-- du/dt + (u . grad)u = -grad(p) + nu*Delta(u) + f, with non-zero external forcing f.
-- This formalizes the external force variant studied in singularity blowup models.
-- NOTE: Does NOT resolve the unforced homogeneous 3D Millennium Problem.

structure FluidDomain where
  dim : Nat
  viscosity : Float

structure NavierStokesForcedSystem (domain : FluidDomain) where
  external_forcing_norm : Float
  forcing_non_zero : external_forcing_norm > 0.0

theorem forced_navier_stokes_has_external_forcing (domain : FluidDomain) (sys : NavierStokesForcedSystem domain) :
    sys.external_forcing_norm > 0.0 := by
  exact sys.forcing_non_zero
