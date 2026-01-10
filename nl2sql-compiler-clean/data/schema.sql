-- ──────────────────────────────────────────────────────────────
--  NL2SQL Compiler — Sample Database Schema
--  Database: nl2sql_db
-- ──────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS nl2sql_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE nl2sql_db;

-- ── Departments ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id          INT           NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)  NOT NULL,
    location    VARCHAR(100)  DEFAULT NULL,
    manager_id  INT           DEFAULT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dept_name (name)
) ENGINE=InnoDB;

-- ── Employees ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    id          INT           NOT NULL AUTO_INCREMENT,
    first_name  VARCHAR(80)   NOT NULL,
    last_name   VARCHAR(80)   NOT NULL,
    email       VARCHAR(150)  NOT NULL,
    phone       VARCHAR(20)   DEFAULT NULL,
    hire_date   DATE          NOT NULL,
    dept_id     INT           DEFAULT NULL,
    job_title   VARCHAR(100)  DEFAULT NULL,
    salary      DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    active      TINYINT(1)    NOT NULL DEFAULT 1,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_email (email),
    KEY idx_dept (dept_id),
    CONSTRAINT fk_emp_dept FOREIGN KEY (dept_id)
        REFERENCES departments(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Add manager FK after employees table exists
ALTER TABLE departments
    ADD CONSTRAINT fk_dept_mgr FOREIGN KEY (manager_id)
        REFERENCES employees(id) ON DELETE SET NULL;

-- ── Customers ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id          INT           NOT NULL AUTO_INCREMENT,
    first_name  VARCHAR(80)   NOT NULL,
    last_name   VARCHAR(80)   NOT NULL,
    email       VARCHAR(150)  NOT NULL,
    city        VARCHAR(100)  DEFAULT NULL,
    country     VARCHAR(80)   DEFAULT 'India',
    phone       VARCHAR(20)   DEFAULT NULL,
    joined_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_cust_email (email),
    KEY idx_city (city)
) ENGINE=InnoDB;

-- ── Products ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id          INT             NOT NULL AUTO_INCREMENT,
    name        VARCHAR(200)    NOT NULL,
    category    VARCHAR(80)     DEFAULT NULL,
    price       DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    stock_qty   INT             NOT NULL DEFAULT 0,
    active      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_category (category)
) ENGINE=InnoDB;

-- ── Orders ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id           INT            NOT NULL AUTO_INCREMENT,
    customer_id  INT            NOT NULL,
    order_date   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status       ENUM('pending','processing','shipped','delivered','cancelled')
                                NOT NULL DEFAULT 'pending',
    total_amount DECIMAL(12,2)  NOT NULL DEFAULT 0.00,
    PRIMARY KEY (id),
    KEY idx_cust   (customer_id),
    KEY idx_date   (order_date),
    KEY idx_status (status),
    CONSTRAINT fk_order_cust FOREIGN KEY (customer_id)
        REFERENCES customers(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ── Order Items ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id          INT             NOT NULL AUTO_INCREMENT,
    order_id    INT             NOT NULL,
    product_id  INT             NOT NULL,
    quantity    INT             NOT NULL DEFAULT 1,
    unit_price  DECIMAL(10,2)   NOT NULL,
    PRIMARY KEY (id),
    KEY idx_order   (order_id),
    KEY idx_product (product_id),
    CONSTRAINT fk_oi_order   FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    CONSTRAINT fk_oi_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ── Salaries (history) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS salaries (
    id          INT             NOT NULL AUTO_INCREMENT,
    employee_id INT             NOT NULL,
    amount      DECIMAL(12,2)   NOT NULL,
    effective   DATE            NOT NULL,
    PRIMARY KEY (id),
    KEY idx_sal_emp (employee_id),
    CONSTRAINT fk_sal_emp FOREIGN KEY (employee_id)
        REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;
