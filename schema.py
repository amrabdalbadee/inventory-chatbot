"""SQL Server schema for the inventory system."""

SCHEMA_DDL = """
-- Core reference tables
CREATE TABLE Customers (
    CustomerId INT IDENTITY PRIMARY KEY,
    CustomerCode VARCHAR(50) UNIQUE NOT NULL,
    CustomerName NVARCHAR(200) NOT NULL,
    Email NVARCHAR(200) NULL,
    Phone NVARCHAR(50) NULL,
    BillingAddress1 NVARCHAR(200) NULL,
    BillingCity NVARCHAR(100) NULL,
    BillingCountry NVARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Vendors (
    VendorId INT IDENTITY PRIMARY KEY,
    VendorCode VARCHAR(50) UNIQUE NOT NULL,
    VendorName NVARCHAR(200) NOT NULL,
    Email NVARCHAR(200) NULL,
    Phone NVARCHAR(50) NULL,
    AddressLine1 NVARCHAR(200) NULL,
    City NVARCHAR(100) NULL,
    Country NVARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Sites (
    SiteId INT IDENTITY PRIMARY KEY,
    SiteCode VARCHAR(50) UNIQUE NOT NULL,
    SiteName NVARCHAR(200) NOT NULL,
    AddressLine1 NVARCHAR(200) NULL,
    City NVARCHAR(100) NULL,
    Country NVARCHAR(100) NULL,
    TimeZone NVARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Locations (
    LocationId INT IDENTITY PRIMARY KEY,
    SiteId INT NOT NULL,
    LocationCode VARCHAR(50) NOT NULL,
    LocationName NVARCHAR(200) NOT NULL,
    ParentLocationId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Locations_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    CONSTRAINT FK_Locations_Parent FOREIGN KEY (ParentLocationId) REFERENCES Locations(LocationId)
);

CREATE TABLE Items (
    ItemId INT IDENTITY PRIMARY KEY,
    ItemCode NVARCHAR(100) UNIQUE NOT NULL,
    ItemName NVARCHAR(200) NOT NULL,
    Category NVARCHAR(100) NULL,
    UnitOfMeasure NVARCHAR(50) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Assets (
    AssetId INT IDENTITY PRIMARY KEY,
    AssetTag VARCHAR(100) UNIQUE NOT NULL,
    AssetName NVARCHAR(200) NOT NULL,
    SiteId INT NOT NULL,
    LocationId INT NULL,
    SerialNumber NVARCHAR(200) NULL,
    Category NVARCHAR(100) NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Active',  -- Active, InRepair, Disposed
    Cost DECIMAL(18,2) NULL,
    PurchaseDate DATE NULL,
    VendorId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT FK_Assets_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    CONSTRAINT FK_Assets_Location FOREIGN KEY (LocationId) REFERENCES Locations(LocationId),
    CONSTRAINT FK_Assets_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

CREATE TABLE Bills (
    BillId INT IDENTITY PRIMARY KEY,
    VendorId INT NOT NULL,
    BillNumber VARCHAR(100) NOT NULL,
    BillDate DATE NOT NULL,
    DueDate DATE NULL,
    TotalAmount DECIMAL(18,2) NOT NULL,
    Currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',  -- Open, Paid, Void
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT FK_Bills_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

CREATE TABLE PurchaseOrders (
    POId INT IDENTITY PRIMARY KEY,
    PONumber VARCHAR(100) NOT NULL,
    VendorId INT NOT NULL,
    PODate DATE NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',  -- Open, Approved, Closed, Cancelled
    SiteId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT FK_PurchaseOrders_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId),
    CONSTRAINT FK_PurchaseOrders_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

CREATE TABLE PurchaseOrderLines (
    POLineId INT IDENTITY PRIMARY KEY,
    POId INT NOT NULL,
    LineNumber INT NOT NULL,
    ItemId INT NULL,
    ItemCode NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200) NULL,
    Quantity DECIMAL(18,4) NOT NULL,
    UnitPrice DECIMAL(18,4) NOT NULL,
    CONSTRAINT FK_PurchaseOrderLines_PO FOREIGN KEY (POId) REFERENCES PurchaseOrders(POId),
    CONSTRAINT FK_PurchaseOrderLines_Item FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
);

CREATE TABLE SalesOrders (
    SOId INT IDENTITY PRIMARY KEY,
    SONumber VARCHAR(100) NOT NULL,
    CustomerId INT NOT NULL,
    SODate DATE NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',  -- Open, Shipped, Closed, Cancelled
    SiteId INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,
    CONSTRAINT FK_SalesOrders_Customer FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId),
    CONSTRAINT FK_SalesOrders_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

CREATE TABLE SalesOrderLines (
    SOLineId INT IDENTITY PRIMARY KEY,
    SOId INT NOT NULL,
    LineNumber INT NOT NULL,
    ItemId INT NULL,
    ItemCode NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200) NULL,
    Quantity DECIMAL(18,4) NOT NULL,
    UnitPrice DECIMAL(18,4) NOT NULL,
    CONSTRAINT FK_SalesOrderLines_SO FOREIGN KEY (SOId) REFERENCES SalesOrders(SOId),
    CONSTRAINT FK_SalesOrderLines_Item FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
);

CREATE TABLE AssetTransactions (
    AssetTxnId INT IDENTITY PRIMARY KEY,
    AssetId INT NOT NULL,
    FromLocationId INT NULL,
    ToLocationId INT NULL,
    TxnType VARCHAR(30) NOT NULL,  -- Move, Adjust, Dispose, Create
    Quantity INT NOT NULL DEFAULT 1,
    TxnDate DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    Note NVARCHAR(500) NULL,
    CONSTRAINT FK_AssetTransactions_Asset FOREIGN KEY (AssetId) REFERENCES Assets(AssetId),
    CONSTRAINT FK_AssetTransactions_FromLoc FOREIGN KEY (FromLocationId) REFERENCES Locations(LocationId),
    CONSTRAINT FK_AssetTransactions_ToLoc FOREIGN KEY (ToLocationId) REFERENCES Locations(LocationId)
);
"""
