/// Autonomous Risk Guardian — on-chain policy contract.
///
/// The off-chain AI crew (FastAPI + CrewAI) holds a GuardianCap and submits
/// transactions here when it produces an approved verdict. Events emitted by
/// each action are indexed by the frontend's ActionLog.
///
/// Three roles:
///   Guardian  — the backend keypair; can adjust params and pause markets.
///   DAO       — a multisig or governance address; can override any state.
///   Anyone    — can read the current RiskParameters via view functions.
module risk_guardian::guardian {
    use sui::event;

    // ── Error codes ───────────────────────────────────────────────────────────

    /// Tried to adjust parameters while the market is paused.
    const EMarketPaused: u64 = 0;
    /// Agent confidence below the 60-point threshold required for execution.
    const ELowConfidence: u64 = 1;
    /// Proposed LTV would exceed the 90 % hard cap.
    const ELtvTooHigh: u64 = 2;
    // ── Capabilities ──────────────────────────────────────────────────────────

    /// Held by the backend server keypair.
    /// Required to call any guardian action.
    public struct GuardianCap has key, store {
        id: UID,
    }

    /// Held by a DAO multisig or governance module.
    /// Required to call dao_override.
    public struct DaoCap has key, store {
        id: UID,
    }

    // ── Shared state ──────────────────────────────────────────────────────────

    /// Shared object — everyone can read; only the guardian can mutate.
    public struct RiskParameters has key {
        id: UID,
        /// Loan-to-value ratio in basis points (7500 = 75 %).
        ltv_bps: u64,
        /// Maximum borrow volume in base units.
        borrow_cap: u64,
        /// Whether the market is currently halted.
        paused: bool,
        /// Human-readable reason set when pausing.
        pause_reason: vector<u8>,
        /// Total number of guardian actions executed.
        action_count: u64,
    }

    // ── Events (read by the frontend ActionLog) ────────────────────────────────

    public struct ParametersAdjusted has copy, drop {
        ltv_bps: u64,
        borrow_cap: u64,
        /// Agent overall_confidence score (0–100).
        confidence: u64,
        /// "BUY" | "SELL" | "HOLD"
        recommendation: vector<u8>,
        action_count: u64,
    }

    public struct MarketPaused has copy, drop {
        reason: vector<u8>,
        action_count: u64,
    }

    public struct MarketResumed has copy, drop {
        by: address,
        action_count: u64,
    }

    public struct DaoOverrideApplied has copy, drop {
        action: vector<u8>,
        by: address,
        action_count: u64,
    }

    // ── Initialiser ───────────────────────────────────────────────────────────

    /// Called once at publish time.
    /// Sends GuardianCap and DaoCap to the publisher, creates shared RiskParameters.
    fun init(ctx: &mut TxContext) {
        transfer::transfer(
            GuardianCap { id: object::new(ctx) },
            tx_context::sender(ctx),
        );

        transfer::transfer(
            DaoCap { id: object::new(ctx) },
            tx_context::sender(ctx),
        );

        transfer::share_object(RiskParameters {
            id: object::new(ctx),
            ltv_bps: 7500,
            borrow_cap: 1_000_000,
            paused: false,
            pause_reason: b"",
            action_count: 0,
        });
    }

    // ── Guardian actions ──────────────────────────────────────────────────────

    /// Adjust LTV and borrow cap based on an approved agent verdict.
    /// Requires confidence >= 60 and ltv_bps <= 9000.
    public fun adjust_parameters(
        _cap: &GuardianCap,
        params: &mut RiskParameters,
        ltv_bps: u64,
        borrow_cap: u64,
        confidence: u64,
        recommendation: vector<u8>,
        _ctx: &mut TxContext,
    ) {
        assert!(!params.paused, EMarketPaused);
        assert!(confidence >= 60, ELowConfidence);
        assert!(ltv_bps <= 9000, ELtvTooHigh);

        params.ltv_bps = ltv_bps;
        params.borrow_cap = borrow_cap;
        params.action_count = params.action_count + 1;

        event::emit(ParametersAdjusted {
            ltv_bps,
            borrow_cap,
            confidence,
            recommendation,
            action_count: params.action_count,
        });
    }

    /// Halt the market. Can be called even when already paused (updates reason).
    public fun pause_market(
        _cap: &GuardianCap,
        params: &mut RiskParameters,
        reason: vector<u8>,
        _ctx: &mut TxContext,
    ) {
        params.paused = true;
        params.pause_reason = reason;
        params.action_count = params.action_count + 1;

        event::emit(MarketPaused {
            reason: params.pause_reason,
            action_count: params.action_count,
        });
    }

    /// Resume a paused market.
    public fun resume_market(
        _cap: &GuardianCap,
        params: &mut RiskParameters,
        ctx: &mut TxContext,
    ) {
        params.paused = false;
        params.pause_reason = b"";
        params.action_count = params.action_count + 1;

        event::emit(MarketResumed {
            by: tx_context::sender(ctx),
            action_count: params.action_count,
        });
    }

    // ── DAO override ──────────────────────────────────────────────────────────

    /// Reset all parameters to safe defaults and unpause.
    /// Only callable by the holder of DaoCap (multisig / governance).
    public fun dao_override(
        _cap: &DaoCap,
        params: &mut RiskParameters,
        action: vector<u8>,
        ctx: &mut TxContext,
    ) {
        params.paused = false;
        params.pause_reason = b"";
        params.ltv_bps = 7500;
        params.borrow_cap = 1_000_000;
        params.action_count = params.action_count + 1;

        event::emit(DaoOverrideApplied {
            action,
            by: tx_context::sender(ctx),
            action_count: params.action_count,
        });
    }

    // ── View functions (read-only) ─────────────────────────────────────────────

    public fun ltv_bps(p: &RiskParameters): u64       { p.ltv_bps }
    public fun borrow_cap(p: &RiskParameters): u64    { p.borrow_cap }
    public fun is_paused(p: &RiskParameters): bool    { p.paused }
    public fun pause_reason(p: &RiskParameters): &vector<u8> { &p.pause_reason }
    public fun action_count(p: &RiskParameters): u64  { p.action_count }
}
