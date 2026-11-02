//! Validated L37 context. Native sherpa owns feature buffering, masks and EOF flushing.
#[derive(Debug, Clone, Copy)]
pub struct ContextPlan {
    pub left_ms: u32,
    pub chunk_ms: u32,
    pub right_ms: u32,
}
impl ContextPlan {
    pub const L37: Self = Self {
        left_ms: 2960,
        chunk_ms: 560,
        right_ms: 560,
    };
    pub fn algorithmic_latency_ms(self) -> u32 {
        self.chunk_ms + self.right_ms
    }
}
#[cfg(test)]
mod tests {
    use super::ContextPlan;
    #[test]
    fn l37_matches_export_metadata() {
        assert_eq!(ContextPlan::L37.left_ms, 37 * 80);
        assert_eq!(ContextPlan::L37.algorithmic_latency_ms(), 1120);
    }
}
