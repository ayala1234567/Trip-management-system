
CREATE TABLE teachers (
    teacher_id VARCHAR(9) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    grade_class VARCHAR(10) NOT NULL
);


CREATE TABLE students (
    student_id VARCHAR(9) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    grade_class VARCHAR(10) NOT NULL,
    assigned_teacher_id VARCHAR(9), 
    CONSTRAINT fk_teacher
        FOREIGN KEY (assigned_teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL 
);


INSERT INTO teachers (teacher_id, full_name, grade_class) VALUES
('012345678', 'Sarah Israeli', 'Grade A-1'),
('087654321', 'Rivka Cohen', 'Grade B-2');

INSERT INTO students (student_id, full_name, grade_class, assigned_teacher_id) VALUES
('111111111', 'Abraham Cohen', 'Grade A-1', '012345678'),
('222222222', 'Isaac Levi', 'Grade A-1', '012345678'),
('333333333', 'Jacob Mizrahi', 'Grade A-1', '012345678'),
('444444444', 'Moses Peretz', 'Grade A-1', '012345678'),
('555555555', 'David Biton', 'Grade A-1', '012345678');

INSERT INTO students (student_id, full_name, grade_class, assigned_teacher_id) VALUES
('666666666', 'Leah Aharoni', 'Grade B-2', '087654321'),
('777777777', 'Rachel Stern', 'Grade B-2', '087654321'),
('888888888', 'Miriam Friedman', 'Grade B-2', '087654321'),
('999999999', 'Hannah Goldberg', 'Grade B-2', '087654321'),
('121212121', 'Esther Weiss', 'Grade B-2', '087654321');


