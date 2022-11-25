CREATE TABLE domain (
    id int PRIMARY KEY,
    name varchar UNIQUE NOT NULL,
    description varchar
);

CREATE FUNCTION chk_domain_id_f (
    @domain_id int,
    @domain_internal_id int,
    @id int
) RETURNS bit AS
BEGIN
    IF EXISTS (
        SELECT Count(*)
        FROM location AS l
        WHERE location.domain_id = l.domain_id
            AND location.domain_internal_id = l.domain_internal_id
            AND location.id <> l.id
    ) RETURN 0
    RETURN 1
END

CREATE FUNCTION chk_within_parent_f(
    @minimum_elevation int,
    @maximum_elevation int,
    @geom geography,
    @parent_id int,
    @parent_valid_from datetime2
) RETURNS bit AS
BEGIN
    DECLARE @p_min_elev int,
            @p_max_elev int,
            @p_geom geography;
    WHILE @parent_id IS NOT NULL
    BEGIN
        SELECT
            @p_min_elev = COALESCE(@p_min_elev, minimum_elevation),
            @p_max_elev = COALESCE(@p_max_elev, maximum_elevation),
            @p_geom = COALESCE(@p_geom, geom),
            @parent_id = parent_id,
            @parent_valid_from = parent_valid_from
        FROM location
        WHERE id = @parent_id AND parent_valid_from = @parent_valid_from;
    END
    IF (
        @p_min_elev > @minimum_elevation
        OR @p_max_elev < @maximum_elevation
        OR (@geom IS NOT NULL AND @p_geom IS NOT NULL AND @geom.STWithin(@p_geom) = 0)
    ) RETURN 0
    RETURN 1
END

CREATE TABLE location (
    id int NOT NULL,
    valid_from datetime2 NOT NULL DEFAULT GETDATE(),
    -- We should probably skip Valid_To, just create a new location with a new Valid_From
    domain_id int FOREIGN KEY REFERENCES domain(id),
    domain_internal_id int,
    parent_id int,
    parent_valid_from datetime2,
    minimum_elevation int,
    maximum_elevation int,
    geom geography,
    PRIMARY KEY (id, valid_from),
    FOREIGN KEY (parent_id, parent_valid_from) REFERENCES location(id, valid_from),
    CONSTRAINT chk_location_domain_id CHECk (
        dbo.chk_domain_id_f(domain_id, domain_internal_id, id) = 1
    ),
    CONSTRAINT chk_domain_id CHECK (
        (domain_id IS NULL AND domain_internal_id IS NULL)
        OR (domain_id IS NOT NULL AND domain_internal_id IS NOT NULL)
    ),
    CONSTRAINT chk_within_parent CHECK (
        geom IS NOT NULL OR COALESCE(minimum_elevation, maximum_elevation) IS NOT NULL
        AND dbo.chk_within_parent_f(
            minimum_elevation,
            maximum_elevation, geom,
            parent_id,
            parent_valid_from
        ) = 1
    )
    -- We should probably make a constraint that checks that updated versions of
    -- regions doesn't conflict with children
);
CREATE SPATIAL INDEX geom_idx ON location(geom);

CREATE TABLE observed_property (
    id int PRIMARY KEY IDENTITY(1,1),
    name varchar UNIQUE NOT NULL,
    description varchar,
    -- Definition varchar, Should this really be here?
    -- I'm not sure we can define properties like that here, at least not formally.
);

CREATE TABLE unit_of_measurement (
    id int PRIMARY KEY IDENTITY(1,1),
    name int UNIQUE NOT NULL,
    description varchar
);

CREATE TABLE statistical_measure (
    id int PRIMARY KEY IDENTITY(1,1),
    name varchar UNIQUE NOT NULL,
    unit_of_measurement_id int NOT NULL,
    description varchar,
    definition varchar, -- I wasn't there when this was added, but I guess it is a reference to a function
                        -- or a very short code snippet.
    FOREIGN KEY (unit_of_measurement_id) REFERENCES unit_of_measurement(id)
);

CREATE TABLE timeseries (
    id int PRIMARY KEY IDENTITY(1,1),
    -- Excluded name and description here as the db structure will make
    -- _a_lot_ of timeseries, so no-one will want to name all off them.
    location_id int NOT NULL,
    location_valid_from datetime2 NOT NULL,
    observed_property_id int NOT NULL,
    statistical_measure_id int NOT NULL,
    FOREIGN KEY (location_id, location_valid_from) REFERENCES location(id, valid_from),
    FOREIGN KEY (observed_property_id) REFERENCES observed_property(id),
    FOREIGN KEY (statistical_measure_id) REFERENCES statistical_measure(id)
);

-- Added Quality, is it not in the sketch for a reason?
CREATE TABLE quality (
    id int PRIMARY KEY IDENTITY(1,1),
    name varchar UNIQUE NOT NULL,
    description varchar
)

CREATE TABLE timeseries_value (
    id bigint PRIMARY KEY IDENTITY(1,1),
    timestamp datetime2 NOT NULL DEFAULT GETDATE(),
    timeseries_id int NOT NULL,
    quality_id int NOT NULL,
    value float, -- Can be NULL NaN or whatever
    FOREIGN KEY (timeseries_id) REFERENCES timeseries(id),
    FOREIGN KEY (quality_id) REFERENCES quality(id)
);

CREATE TABLE customer (
    id int PRIMARY KEY IDENTITY(1,1),
    name varchar UNIQUE NOT NULL,
    description varchar
);

CREATE TABLE job (
    id int PRIMARY KEY IDENTITY(1,1),
    order_date datetime2 NOT NULL DEFAULT GETDATE(),
    delivery_id int, -- What is this?
    customer_id int,
    FOREIGN KEY (customer_id) REFERENCES customer(id)
);

CREATE TABLE jobconfig (
    id int PRIMARY KEY IDENTITY(1,1),
    location_id int NOT NULL,
    location_valid_from datetime2 NOT NULL,
    include_child_locations bit NOT NULL,
    observed_property_id int NOT NULL, -- This does not make the script do anything,
                                       -- it describes what the script does.
    statistical_measure_ids varchar NOT NULL, -- This can actually be sent to the script.
                                              -- Since this can be many measures, and T-SQL does not have a list type
                                              -- we either need to normalize this into its own table or make a
                                              -- comma separated string with a constraint or something.
    script varchar NOT NULL, -- Some reference
    FOREIGN KEY (location_id, location_valid_from) REFERENCES location(id, valid_from),
    FOREIGN KEY (observed_property_id) REFERENCES observed_property(id),
    -- Constraint for StatisticalMeasure_Ids
);
