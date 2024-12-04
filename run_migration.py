from migrations.update_services_schema import upgrade

if __name__ == '__main__':
    upgrade()
    print("Migration completed successfully!") 