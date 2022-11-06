use std::io::{BufReader, BufWriter};

use ariadne::{Label, Report, ReportKind, Source};
use pyo3::prelude::*;

#[pyfunction]
fn format_error(input: String) -> PyResult<String> {
    let buf = Vec::new();
    let mut writer = BufWriter::new(buf);
    Report::build(ReportKind::Error, (), 34)
        .with_message("Incompatible types")
        .with_label(Label::new(32..33).with_message("This is of type Nat"))
        .with_label(Label::new(42..45).with_message("This is of type Str"))
        .finish()
        .write(Source::from(input), &mut writer);
    PyResult::Ok(String::from_utf8(Vec::from(writer.buffer())).unwrap())
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn ariadne_wrapper(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(format_error, m)?)?;
    Ok(())
}