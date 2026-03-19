// Copyright 2026 by DTS, The State of Utah

use wasm_bindgen::prelude::*;

/// A 3-component vector for 3D geometry operations.
#[wasm_bindgen]
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Vec3 {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

#[wasm_bindgen]
impl Vec3 {
    #[wasm_bindgen(constructor)]
    pub fn new(x: f64, y: f64, z: f64) -> Vec3 {
        Vec3 { x, y, z }
    }

    /// Returns the length (magnitude) of the vector.
    pub fn length(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    /// Returns a normalized (unit) copy of this vector.
    pub fn normalize(&self) -> Vec3 {
        let len = self.length();
        if len == 0.0 {
            return Vec3::new(0.0, 0.0, 0.0);
        }
        Vec3::new(self.x / len, self.y / len, self.z / len)
    }

    /// Returns the dot product of this vector and another.
    pub fn dot(&self, other: &Vec3) -> f64 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    /// Returns the cross product of this vector and another.
    pub fn cross(&self, other: &Vec3) -> Vec3 {
        Vec3::new(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )
    }

    /// Adds another vector to this one, returning a new vector.
    pub fn add(&self, other: &Vec3) -> Vec3 {
        Vec3::new(self.x + other.x, self.y + other.y, self.z + other.z)
    }

    /// Subtracts another vector from this one, returning a new vector.
    pub fn sub(&self, other: &Vec3) -> Vec3 {
        Vec3::new(self.x - other.x, self.y - other.y, self.z - other.z)
    }

    /// Scales this vector by a scalar, returning a new vector.
    pub fn scale(&self, s: f64) -> Vec3 {
        Vec3::new(self.x * s, self.y * s, self.z * s)
    }
}

/// A 4x4 column-major transformation matrix for 3D operations.
#[wasm_bindgen]
pub struct Mat4 {
    data: [f64; 16],
}

#[wasm_bindgen]
impl Mat4 {
    /// Creates an identity matrix.
    #[wasm_bindgen(constructor)]
    pub fn identity() -> Mat4 {
        Mat4 {
            #[rustfmt::skip]
            data: [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
        }
    }

    /// Returns the matrix data as a flat Float64Array-compatible JS value.
    pub fn to_js_array(&self) -> Vec<f64> {
        self.data.to_vec()
    }

    /// Creates a perspective projection matrix.
    pub fn perspective(fov_y: f64, aspect: f64, near: f64, far: f64) -> Mat4 {
        let f = 1.0 / (fov_y / 2.0).tan();
        let nf = 1.0 / (near - far);
        Mat4 {
            #[rustfmt::skip]
            data: [
                f / aspect, 0.0, 0.0,                          0.0,
                0.0,        f,   0.0,                          0.0,
                0.0,        0.0, (far + near) * nf,           -1.0,
                0.0,        0.0, 2.0 * far * near * nf,        0.0,
            ],
        }
    }

    /// Creates a rotation matrix around the Y axis (in radians).
    pub fn rotation_y(angle: f64) -> Mat4 {
        let c = angle.cos();
        let s = angle.sin();
        Mat4 {
            #[rustfmt::skip]
            data: [
                 c,  0.0, s,  0.0,
                0.0, 1.0, 0.0, 0.0,
                -s,  0.0, c,  0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
        }
    }

    /// Creates a translation matrix.
    pub fn translation(x: f64, y: f64, z: f64) -> Mat4 {
        Mat4 {
            #[rustfmt::skip]
            data: [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                x,   y,   z,   1.0,
            ],
        }
    }

    /// Multiplies this matrix by another, returning a new matrix.
    pub fn multiply(&self, other: &Mat4) -> Mat4 {
        let a = &self.data;
        let b = &other.data;
        let mut result = [0.0f64; 16];
        for row in 0..4 {
            for col in 0..4 {
                for k in 0..4 {
                    result[row * 4 + col] += a[row * 4 + k] * b[k * 4 + col];
                }
            }
        }
        Mat4 { data: result }
    }
}

/// Computes the Euclidean distance between two 3D points.
#[wasm_bindgen]
pub fn distance(a: &Vec3, b: &Vec3) -> f64 {
    a.sub(b).length()
}

/// Returns a greeting string (health-check export).
#[wasm_bindgen]
pub fn greet(name: &str) -> String {
    format!("Hello from ggp3d WASM, {}!", name)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vec3_length() {
        let v = Vec3::new(3.0, 4.0, 0.0);
        assert!((v.length() - 5.0).abs() < 1e-10);
    }

    #[test]
    fn test_vec3_normalize() {
        let v = Vec3::new(0.0, 5.0, 0.0);
        let n = v.normalize();
        assert!((n.x).abs() < 1e-10);
        assert!((n.y - 1.0).abs() < 1e-10);
        assert!((n.z).abs() < 1e-10);
    }

    #[test]
    fn test_vec3_dot() {
        let a = Vec3::new(1.0, 0.0, 0.0);
        let b = Vec3::new(0.0, 1.0, 0.0);
        assert!((a.dot(&b)).abs() < 1e-10);
    }

    #[test]
    fn test_vec3_cross() {
        let a = Vec3::new(1.0, 0.0, 0.0);
        let b = Vec3::new(0.0, 1.0, 0.0);
        let c = a.cross(&b);
        assert!((c.x).abs() < 1e-10);
        assert!((c.y).abs() < 1e-10);
        assert!((c.z - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_distance() {
        let a = Vec3::new(0.0, 0.0, 0.0);
        let b = Vec3::new(1.0, 1.0, 1.0);
        assert!((distance(&a, &b) - 3.0f64.sqrt()).abs() < 1e-10);
    }

    #[test]
    fn test_mat4_identity() {
        let m = Mat4::identity();
        let arr = m.to_js_array();
        assert_eq!(arr[0], 1.0);
        assert_eq!(arr[5], 1.0);
        assert_eq!(arr[10], 1.0);
        assert_eq!(arr[15], 1.0);
        assert_eq!(arr[1], 0.0);
    }
}
